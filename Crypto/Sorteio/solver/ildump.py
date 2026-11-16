#!/usr/bin/env python3
# Minimal ECMA-335 metadata + CIL disassembler for a single tiny .NET assembly.
# Enough to dump method IL with resolved call/field/string tokens. No deps.
import sys, struct

def u8(b,o):  return b[o]
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]

class PE:
    def __init__(self, data):
        self.d = data
        e_lfanew = u32(data,0x3c)
        assert data[e_lfanew:e_lfanew+4]==b'PE\x00\x00'
        coff = e_lfanew+4
        self.nsec = u16(data,coff+2)
        opt = coff+20
        magic = u16(data,opt)
        self.pe32plus = (magic==0x20b)
        # data directories offset
        dd = opt + (112 if self.pe32plus else 96)
        self.num_dd = u32(data, opt + (108 if self.pe32plus else 92))
        self.datadirs = []
        for i in range(self.num_dd):
            self.datadirs.append((u32(data,dd+i*8), u32(data,dd+i*8+4)))
        sec = dd + self.num_dd*8
        self.sections=[]
        for i in range(self.nsec):
            o=sec+i*40
            name=data[o:o+8].rstrip(b'\x00')
            vsize=u32(data,o+8); vaddr=u32(data,o+12)
            rsize=u32(data,o+16); raddr=u32(data,o+20)
            self.sections.append((name,vaddr,vsize,raddr,rsize))
    def rva2off(self, rva):
        for name,va,vs,ra,rs in self.sections:
            if va<=rva<va+max(vs,rs):
                return ra+(rva-va)
        raise ValueError("rva %x not mapped"%rva)

# ---- Metadata tables ----
TNAMES = {0:'Module',1:'TypeRef',2:'TypeDef',4:'Field',6:'MethodDef',8:'Param',
9:'InterfaceImpl',10:'MemberRef',11:'Constant',12:'CustomAttribute',13:'FieldMarshal',
14:'DeclSecurity',15:'ClassLayout',16:'FieldLayout',17:'StandAloneSig',18:'EventMap',
20:'Event',21:'PropertyMap',23:'Property',24:'MethodSemantics',25:'MethodImpl',
26:'ModuleRef',27:'TypeSpec',28:'ImplMap',29:'FieldRVA',32:'Assembly',
35:'AssemblyRef',38:'File',39:'ExportedType',40:'ManifestResource',41:'NestedClass',
42:'GenericParam',44:'GenericParamConstraint',
30:'EncLog',31:'EncMap',19:'Unused19',22:'Unused22',33:'AssemblyProcessor',
34:'AssemblyOS',36:'AssemblyRefProcessor',37:'AssemblyRefOS',43:'MethodSpec'}

# coded index token tables (tag bits, [table ids])
CODED = {
 'TypeDefOrRef':(2,[2,1,27]),
 'HasConstant':(2,[4,8,23]),
 'HasCustomAttribute':(5,[6,4,1,2,8,9,10,0,14,17,20,23,21,24,25,26,27,32,35,38,39,40,42,44,43]),
 'HasFieldMarshal':(1,[4,8]),
 'HasDeclSecurity':(2,[2,6,32]),
 'MemberRefParent':(3,[2,1,26,6,27]),
 'HasSemantics':(1,[20,23]),
 'MethodDefOrRef':(1,[6,10]),
 'MemberForwarded':(1,[4,6]),
 'Implementation':(2,[38,39,40]),
 'CustomAttributeType':(3,[-1,-1,6,10,-1]),
 'ResolutionScope':(2,[0,26,35,1]),
 'TypeOrMethodDef':(1,[2,6]),
}

class MD:
    def __init__(self, pe):
        self.pe=pe; d=pe.d
        clr_rva,clr_sz = pe.datadirs[14]
        o = pe.rva2off(clr_rva)
        md_rva = u32(d,o+8); md_sz=u32(d,o+12)
        mo = pe.rva2off(md_rva)
        assert u32(d,mo)==0x424A5342, "bad metadata sig"
        verlen = u32(d,mo+12)
        p = mo+16+verlen
        p += 2  # flags
        nstreams = u16(d,p); p+=2
        self.streams={}
        for _ in range(nstreams):
            off=u32(d,p); size=u32(d,p+4); p+=8
            name=b''
            while d[p]!=0: name+=bytes([d[p]]); p+=1
            p+=1
            while p%4: p+=1
            self.streams[name.decode()] = (mo+off, size)
        self.strings = self.streams.get('#Strings')
        self.us = self.streams.get('#US')
        self.blob = self.streams.get('#Blob')
        self._parse_tables()
    def getstr(self, idx):
        o,sz=self.strings; d=self.pe.d; s=o+idx; e=d.index(0,s); return d[s:e].decode('utf-8','replace')
    def getus(self, idx):
        # #US: compressed length prefix, then UTF-16LE, last byte flag
        o,sz=self.us; d=self.pe.d; p=o+idx
        b0=d[p]
        if b0<0x80: ln=b0; p+=1
        elif b0<0xC0: ln=((b0&0x3f)<<8)|d[p+1]; p+=2
        else: ln=((b0&0x1f)<<24)|(d[p+1]<<16)|(d[p+2]<<8)|d[p+3]; p+=4
        raw=d[p:p+ln]
        if ln and ln%2==1: raw=raw[:-1]
        return raw.decode('utf-16-le','replace')
    def _parse_tables(self):
        d=self.pe.d; o,sz=self.streams['#~']
        heapsizes=d[o+6]
        self.sidx = 4 if heapsizes&1 else 2
        self.gidx = 4 if heapsizes&2 else 2
        self.bidx = 4 if heapsizes&4 else 2
        valid=struct.unpack_from('<Q',d,o+8)[0]
        p=o+24
        self.rows={}
        present=[i for i in range(64) if (valid>>i)&1]
        for i in present:
            self.rows[i]=u32(d,p); p+=4
        # column schema builder
        def simple(t): return 4 if self.rows.get(t,0)>=65536 else 2
        def coded(name):
            tag,tabs=CODED[name]
            m=max((self.rows.get(t,0) for t in tabs if t>=0), default=0)
            return 4 if m >= (1<<(16-tag)) else 2
        S=self.sidx; G=self.gidx; B=self.bidx
        # schema: each col -> size
        def sch(i):
            r=[]
            if i==0:   r=[2,S,G,G,G]
            elif i==1: r=[coded('ResolutionScope'),S,S]
            elif i==2: r=[4,S,S,coded('TypeDefOrRef'),simple(4),simple(6)]
            elif i==4: r=[2,S,B]
            elif i==6: r=[4,2,2,S,B,simple(8)]
            elif i==8: r=[2,2,S]
            elif i==9: r=[simple(2),coded('TypeDefOrRef')]
            elif i==10:r=[coded('MemberRefParent'),S,B]
            elif i==11:r=[2,coded('HasConstant'),B]  # (1 byte type + pad) -> actually 1+1
            elif i==12:r=[coded('HasCustomAttribute'),coded('CustomAttributeType'),B]
            elif i==13:r=[coded('HasFieldMarshal'),B]
            elif i==14:r=[2,coded('HasDeclSecurity'),B]
            elif i==15:r=[2,2,simple(2)]
            elif i==16:r=[4,simple(4)]
            elif i==17:r=[B]
            elif i==18:r=[simple(2),simple(20),simple(23)]
            elif i==20:r=[2,S,coded('TypeDefOrRef')]
            elif i==21:r=[simple(2),simple(23)]
            elif i==23:r=[2,S,B]
            elif i==24:r=[2,coded('MethodDefOrRef'),coded('HasSemantics')]
            elif i==25:r=[simple(2),coded('MethodDefOrRef'),coded('MethodDefOrRef')]
            elif i==26:r=[S]
            elif i==27:r=[B]
            elif i==28:r=[2,coded('MemberForwarded'),S,simple(26)]
            elif i==29:r=[4,simple(4)]
            elif i==32:r=[4,2,2,2,2,4,B,S,S]
            elif i==35:r=[2,2,2,2,4,B,S,S,B]
            elif i==38:r=[4,S,B]
            elif i==39:r=[4,4,S,S,coded('Implementation')]
            elif i==40:r=[4,4,S,coded('Implementation')]
            elif i==41:r=[simple(2),simple(2)]
            elif i==42:r=[2,2,coded('TypeOrMethodDef'),S]
            elif i==43:r=[coded('MethodDefOrRef'),B]
            elif i==44:r=[simple(42),coded('TypeDefOrRef')]
            elif i==30:r=[4,4]
            elif i==31:r=[4]
            elif i==33:r=[4]
            elif i==34:r=[4,4,4]
            elif i==36:r=[4]
            elif i==37:r=[4,4,4]
            else: raise ValueError('unknown table %d'%i)
            # fix table 11 Constant: 1-byte Type + 1-byte pad
            return r
        # table 11 special-case handled below
        self.tbl_off={}; self.tbl_rowsz={}
        for i in present:
            cols=sch(i)
            if i==11:
                rowsz = 1+1+coded('HasConstant')+B
            else:
                rowsz=sum(cols)
            self.tbl_off[i]=p
            self.tbl_rowsz[i]=rowsz
            self.tbl_cols=getattr(self,'tbl_cols',{})
            self.tbl_cols[i]=cols
            p += rowsz*self.rows[i]
    def row_raw(self,tbl,rid):  # rid 1-based
        off=self.tbl_off[tbl]+(rid-1)*self.tbl_rowsz[tbl]
        return off
    def read_cols(self,tbl,rid):
        d=self.pe.d; cols=self.tbl_cols[tbl]; off=self.row_raw(tbl,rid); vals=[]
        if tbl==11:
            widths=[1,1,CODED and (4 if self.rows.get(max(CODED['HasConstant'][1]),0) else 2)]
        for w in cols:
            if w==2: vals.append(u16(d,off)); off+=2
            elif w==4: vals.append(u32(d,off)); off+=4
            elif w==1: vals.append(u8(d,off)); off+=1
        return vals

def decode_coded(val, name):
    tag,tabs=CODED[name]; mask=(1<<tag)-1
    t=tabs[val&mask]; rid=val>>tag
    return t,rid

# ---- IL opcode map (subset, common ones) ----
OP1={0x00:'nop',0x01:'break',0x02:'ldarg.0',0x03:'ldarg.1',0x04:'ldarg.2',0x05:'ldarg.3',
0x06:'ldloc.0',0x07:'ldloc.1',0x08:'ldloc.2',0x09:'ldloc.3',0x0a:'stloc.0',0x0b:'stloc.1',
0x0c:'stloc.2',0x0d:'stloc.3',0x14:'ldnull',0x15:'ldc.i4.m1',0x16:'ldc.i4.0',0x17:'ldc.i4.1',
0x18:'ldc.i4.2',0x19:'ldc.i4.3',0x1a:'ldc.i4.4',0x1b:'ldc.i4.5',0x1c:'ldc.i4.6',0x1d:'ldc.i4.7',
0x1e:'ldc.i4.8',0x25:'dup',0x26:'pop',0x2a:'ret',0x6a:'conv.i8',0x69:'conv.i4',0x8e:'ldlen',
0x58:'add',0x59:'sub',0x5a:'mul',0x5b:'div',0x5d:'rem',0x5f:'and',0x60:'or',0x61:'xor',
0x62:'shl',0x63:'shr',0x64:'shr.un',0x66:'not',0x65:'neg',0xd3:'conv.i',
0x9a:'ldelem.ref',0x9b:'ldelem.i1'}
# branch/int shorts
OP_S={0x0e:'ldarg.s',0x0f:'ldarga.s',0x10:'starg.s',0x11:'ldloc.s',0x12:'ldloca.s',
0x13:'stloc.s',0x1f:'ldc.i4.s',0x2b:'br.s',0x2c:'brfalse.s',0x2d:'brtrue.s',0x2e:'beq.s',
0x2f:'bge.s',0x30:'bgt.s',0x31:'ble.s',0x32:'blt.s',0x33:'bne.un.s',0x37:'bgt.un.s',0x3b:'blt.un.s'}
OP_I4={0x20:'ldc.i4',0x22:'ldc.r4'}
OP_TOK={0x28:'call',0x6f:'callvirt',0x73:'newobj',0x7b:'ldfld',0x7d:'stfld',0x7e:'ldsfld',
0x80:'stsfld',0x72:'ldstr',0x8d:'newarr',0xa2:'stelem.ref',0x25:'dup',0xfe:'pfx',0x6e:'ldc.i8'}
OP_BR={0x38:'br',0x39:'brfalse',0x3a:'brtrue',0x3b:'blt'}

def main():
    path=sys.argv[1]
    data=open(path,'rb').read()
    pe=PE(data); md=MD(pe)
    d=pe.d
    # Build MethodDef name list + bodies. MethodDef cols: RVA(4),Impl(2),Flags(2),Name(str),Sig(blob),ParamList
    cols=md.tbl_cols[6]; nrows=md.rows[6]
    # TypeDef owns method ranges via MethodList
    tcols=md.tbl_cols[2]; tn=md.rows[2]
    types=[]
    for r in range(1,tn+1):
        v=md.read_cols(2,r)
        # cols: Flags(4),Name(str),Ns(str),Extends(coded),FieldList,MethodList
        types.append((md.getstr(v[1]), v[5]))
    def type_of_method(mi):  # mi 1-based
        owner='?'
        for idx,(name,mlist) in enumerate(types):
            nextm = types[idx+1][1] if idx+1<len(types) else nrows+1
            if mlist<=mi<nextm: return name
        return owner
    def method_name(rid):
        v=md.read_cols(6,rid); return md.getstr(v[3]), v[0]  # name, rva
    def memberref_name(rid):
        v=md.read_cols(10,rid)  # Parent(coded),Name(str),Sig(blob)
        t,prid=decode_coded(v[0],'MemberRefParent')
        pname='?'
        if t==1: pname=typeref_name(prid)
        elif t==27: pname='TypeSpec#%d'%prid
        elif t==6: pname=method_name(prid)[0]
        return '%s::%s'%(pname, md.getstr(v[1]))
    def typeref_name(rid):
        v=md.read_cols(1,rid)  # ResolutionScope,Name,Ns
        ns=md.getstr(v[2]); nm=md.getstr(v[1])
        return (ns+'.'+nm) if ns else nm
    def field_name(rid):
        v=md.read_cols(4,rid); return md.getstr(v[1])
    def resolve_token(tok):
        tbl=tok>>24; rid=tok&0xffffff
        if tbl==0x0a: return memberref_name(rid)
        if tbl==0x06: return 'M:'+type_of_method(rid)+'::'+method_name(rid)[0]
        if tbl==0x04: return 'F:'+field_name(rid)
        if tbl==0x01: return 'T:'+typeref_name(rid)
        if tbl==0x1b: return 'TypeSpec#%d'%rid
        if tbl==0x70: return 'STR:"%s"'%md.getus(rid)
        return '%08x'%tok
    # disassemble selected types
    want = set(sys.argv[2:]) or {'DrawEngine','DrawOutcome','Team','GameSession','DrawState'}
    for rid in range(1,nrows+1):
        name,rva=method_name(rid); owner=type_of_method(rid)
        if owner not in want: continue
        print('\n=== %s::%s  (rva=0x%x) ==='%(owner,name,rva))
        if rva==0: print('  <abstract/extern>'); continue
        off=pe.rva2off(rva); hb=d[off]
        if (hb&3)==2:
            codesz=hb>>2; ilstart=off+1
        else:
            flags=u16(d,off); codesz=u32(d,off+4); ilstart=off+12
        il=d[ilstart:ilstart+codesz]
        disasm(il, resolve_token)

def disasm(il, resolve):
    i=0; n=len(il)
    while i<n:
        pc=i; b=il[i]; i+=1
        if b==0xfe:
            b2=il[i]; i+=1
            names={0x01:'ceq',0x02:'cgt',0x03:'cgt.un',0x04:'clt',0x05:'clt.un',0x09:'ldarg',
                   0x0a:'ldarga',0x0b:'starg',0x0c:'ldloc',0x0d:'ldloca',0x0e:'stloc',0x16:'constrained.',
                   0x15:'initobj',0x1d:'rethrow',0x17:'cpblk',0x14:'ldftn',0x06:'ldftn2'}
            nm=names.get(b2,'fe%02x'%b2)
            if b2 in (0x09,0x0a,0x0b,0x0c,0x0d,0x0e):
                v=u16(il,i); i+=2; print('  IL_%04x: %s %d'%(pc,nm,v))
            elif b2 in (0x15,0x16,0x14,0x06):
                tok=u32(il,i); i+=4; print('  IL_%04x: %s %s'%(pc,nm,resolve(tok)))
            else:
                print('  IL_%04x: %s'%(pc,nm))
            continue
        if b in OP1: print('  IL_%04x: %s'%(pc,OP1[b])); continue
        if b in OP_S:
            v=il[i]; i+=1
            if OP_S[b].endswith('.s') and b in (0x2b,0x2c,0x2d,0x2e,0x2f,0x30,0x31,0x32,0x33,0x37,0x3b):
                tgt=i+((v-256) if v>127 else v); print('  IL_%04x: %s IL_%04x'%(pc,OP_S[b],tgt))
            else:
                sv=v-256 if (b==0x1f and v>127) else v
                print('  IL_%04x: %s %d'%(pc,OP_S[b],sv))
            continue
        if b==0x20: v=u32(il,i); i+=4; print('  IL_%04x: ldc.i4 %d'%(pc,v if v<2**31 else v-2**32)); continue
        if b==0x21: v=struct.unpack_from('<q',il,i)[0]; i+=8; print('  IL_%04x: ldc.i8 %d'%(pc,v)); continue
        if b==0x6e: v=struct.unpack_from('<q',il,i)[0]; i+=8; print('  IL_%04x: ldc.i8 %d'%(pc,v)); continue
        if b==0x23: v=struct.unpack_from('<d',il,i)[0]; i+=8; print('  IL_%04x: ldc.r8 %g'%(pc,v)); continue
        if b in (0x28,0x6f,0x73,0x7b,0x7d,0x7e,0x80,0x72,0x8d,0x74):
            tok=u32(il,i); i+=4
            nm={0x28:'call',0x6f:'callvirt',0x73:'newobj',0x7b:'ldfld',0x7d:'stfld',
                0x7e:'ldsfld',0x80:'stsfld',0x72:'ldstr',0x8d:'newarr',0x74:'castclass'}[b]
            print('  IL_%04x: %s %s'%(pc,nm,resolve(tok))); continue
        if b in (0x38,0x39,0x3a,0x3b,0x3c,0x3d,0x3e,0x3f,0x40,0x41,0x42,0x43,0x44,0x45):
            v=struct.unpack_from('<i',il,i)[0]; i+=4
            nm={0x38:'br',0x39:'brfalse',0x3a:'brtrue',0x3b:'beq',0x3c:'bge',0x3d:'bgt',
                0x3e:'ble',0x3f:'blt',0x40:'bne.un',0x41:'bge.un',0x42:'bgt.un',0x43:'ble.un',0x44:'blt.un'}.get(b,'br?')
            print('  IL_%04x: %s IL_%04x'%(pc,nm,i+v)); continue
        print('  IL_%04x: .byte 0x%02x'%(pc,b))

if __name__=='__main__':
    main()
