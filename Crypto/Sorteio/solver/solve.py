#!/usr/bin/env python3
# Sorteio solver: reproduce .NET System.Random(int seed) and find the Unix
# seconds W where the draw yields 42 (the winning number).
#   draw number = (Random(seedSeconds).Next() % 1000) + 1  == 42  <=>  Next()%1000 == 41
# Seed = (int) DateTimeOffset.UtcNow.ToUnixTimeSeconds().
import sys, datetime, zoneinfo

MBIG = 2147483647
MSEED = 161803398

def net_random_first_next(seed):
    """Return Random(seed).Next() — first InternalSample() of .NET legacy PRNG."""
    seed &= 0xffffffff
    if seed >= 0x80000000:  # interpret as signed int32
        seed -= 0x100000000
    subtraction = MBIG if seed == -2147483648 else abs(seed)
    mj = MSEED - subtraction
    sa = [0]*56
    sa[55] = mj
    mk = 1
    for i in range(1,55):
        ii = (21*i) % 55
        sa[ii] = mk
        mk = mj - mk
        if mk < 0: mk += MBIG
        mj = sa[ii]
    for _ in range(1,5):
        for i in range(1,56):
            sa[i] -= sa[1 + (i+30)%55]
            if sa[i] < 0: sa[i] += MBIG
    inext, inextp = 0, 21
    # one InternalSample:
    inext += 1
    if inext >= 56: inext = 1
    inextp += 1
    if inextp >= 56: inextp = 1
    ret = sa[inext] - sa[inextp]
    if ret == MBIG: ret -= 1
    if ret < 0: ret += MBIG
    return ret

def draw_for_seed(sec):
    return (net_random_first_next(sec) % 1000) + 1

def self_test():
    assert net_random_first_next(0) == 1559595546, net_random_first_next(0)
    assert net_random_first_next(1) == 534011718, net_random_first_next(1)
    # second arg ignored here; just confirm determinism
    print("[selftest] .NET Random(0).Next()=1559595546 OK, Random(1).Next()=534011718 OK")

def verify(pairs):
    """pairs like 'HH:MM:SS=NUM' (BRT): predicted draw for that click-second vs observed.
    Observed number of a draw == f(second of the PREVIOUS click/turn-start). So feed the
    second a draw was CLICKED and the number the NEXT draw showed, OR just check f(sec)."""
    tz = zoneinfo.ZoneInfo("America/Sao_Paulo")
    today = datetime.datetime.now(tz).date()
    for p in pairs:
        hms, num = p.split('=')
        h,m,s = map(int, hms.split(':'))
        dt = datetime.datetime(today.year,today.month,today.day,h,m,s,tzinfo=tz)
        sec = int(dt.timestamp())
        pred = draw_for_seed(sec)
        for off in (-2,-1,0,1,2):
            if draw_for_seed(sec+off) == int(num):
                print(f"  click {hms} (unix {sec}): f(seed)={pred}; observed {num} matches seed offset {off:+d}s")
                break
        else:
            print(f"  click {hms} (unix {sec}): f(seed)={pred}; observed {num} NO match within ±2s")

def main():
    self_test()
    TARGET = 42
    tz = zoneinfo.ZoneInfo("America/Sao_Paulo")
    if len(sys.argv) >= 2 and sys.argv[1] == "verify":
        verify(sys.argv[2:]); return
    # scan window: args = start_iso_local end_iso_local  (default: now -> now+48h)
    if len(sys.argv) >= 3:
        start = datetime.datetime.fromisoformat(sys.argv[1]).replace(tzinfo=tz)
        end   = datetime.datetime.fromisoformat(sys.argv[2]).replace(tzinfo=tz)
    else:
        now = datetime.datetime.now(tz)
        start = now
        end = now + datetime.timedelta(hours=48)
    s0 = int(start.timestamp()); s1 = int(end.timestamp())
    print(f"[scan] {start.isoformat()}  ->  {end.isoformat()}  ({s1-s0} seconds)")
    wins = [s for s in range(s0, s1+1) if draw_for_seed(s) == TARGET]
    print(f"[result] winning seconds (draw==42): {len(wins)} found  (~1/1000 density)\n")
    for s in wins:
        dt_local = datetime.datetime.fromtimestamp(s, tz)
        dt_utc = datetime.datetime.fromtimestamp(s, datetime.timezone.utc)
        print(f"  unix={s}  BRT={dt_local.strftime('%Y-%m-%d %H:%M:%S')}  UTC={dt_utc.strftime('%H:%M:%S')}")
    # also show mean gap
    if len(wins) >= 2:
        gaps = [wins[i+1]-wins[i] for i in range(len(wins)-1)]
        print(f"\n[gaps] min={min(gaps)}s max={max(gaps)}s avg={sum(gaps)//len(gaps)}s")

if __name__ == "__main__":
    main()
