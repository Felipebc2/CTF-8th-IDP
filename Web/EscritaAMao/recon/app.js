(function () {
    "use strict";

    const LARGURA = 900;
    const ALTURA = 300;
    const ESPESSURA = 7;

    const canvas = document.getElementById("quadro");
    const ctx = canvas.getContext("2d");
    const placeholder = document.getElementById("placeholder");
    const btnDesfazer = document.getElementById("btn-desfazer");
    const btnLimpar = document.getElementById("btn-limpar");
    const btnReconhecer = document.getElementById("btn-reconhecer");
    const btnSalvar = document.getElementById("btn-salvar");
    const saidaTexto = document.getElementById("texto-reconhecido");
    const mensagem = document.getElementById("mensagem");
    const listaArquivos = document.getElementById("lista-arquivos");
    const btnMenu = document.getElementById("btn-menu");
    const menu = document.getElementById("menu");

    let tracos = [];
    let tracoAtual = null;
    let ponteiroAtivo = null;
    let ultimoId = null;
    let ocupado = false;

    // ---------- Menu ----------

    btnMenu.addEventListener("click", function () {
        const aberto = menu.classList.toggle("aberto");
        btnMenu.setAttribute("aria-expanded", aberto ? "true" : "false");
    });

    menu.addEventListener("click", function (ev) {
        if (ev.target.tagName === "A") {
            menu.classList.remove("aberto");
            btnMenu.setAttribute("aria-expanded", "false");
        }
    });

    // ---------- Canvas ----------

    function prepararContexto() {
        ctx.lineWidth = ESPESSURA;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.strokeStyle = "#000000";
        ctx.fillStyle = "#000000";
    }

    function pintarFundo() {
        ctx.save();
        ctx.globalCompositeOperation = "source-over";
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, LARGURA, ALTURA);
        ctx.restore();
    }

    function desenharTraco(pontos) {
        if (pontos.length === 0) {
            return;
        }
        if (pontos.length === 1) {
            ctx.beginPath();
            ctx.arc(pontos[0].x, pontos[0].y, ESPESSURA / 2, 0, Math.PI * 2);
            ctx.fill();
            return;
        }
        ctx.beginPath();
        ctx.moveTo(pontos[0].x, pontos[0].y);
        for (let i = 1; i < pontos.length; i++) {
            ctx.lineTo(pontos[i].x, pontos[i].y);
        }
        ctx.stroke();
    }

    function redesenhar() {
        pintarFundo();
        prepararContexto();
        tracos.forEach(desenharTraco);
        if (tracoAtual) {
            desenharTraco(tracoAtual);
        }
    }

    function atualizarEstado() {
        const temTraco = tracos.length > 0;
        placeholder.classList.toggle("oculto", temTraco || tracoAtual !== null);
        btnDesfazer.disabled = !temTraco || ocupado;
        btnLimpar.disabled = !temTraco || ocupado;
        btnReconhecer.disabled = !temTraco || ocupado;
    }

    function coordenadas(ev) {
        const r = canvas.getBoundingClientRect();
        return {
            x: (ev.clientX - r.left) * (LARGURA / r.width),
            y: (ev.clientY - r.top) * (ALTURA / r.height)
        };
    }

    canvas.addEventListener("pointerdown", function (ev) {
        if (ponteiroAtivo !== null || ocupado) {
            return;
        }
        if (ev.pointerType === "mouse" && ev.button !== 0) {
            return;
        }
        ev.preventDefault();
        ponteiroAtivo = ev.pointerId;
        try {
            canvas.setPointerCapture(ev.pointerId);
        } catch (e) {
            // sem captura, segue normalmente
        }
        tracoAtual = [coordenadas(ev)];
        placeholder.classList.add("oculto");
        redesenhar();
    });

    canvas.addEventListener("pointermove", function (ev) {
        if (ev.pointerId !== ponteiroAtivo || !tracoAtual) {
            return;
        }
        ev.preventDefault();
        const eventos = typeof ev.getCoalescedEvents === "function" ? ev.getCoalescedEvents() : [];
        const lista = eventos.length ? eventos : [ev];
        const anterior = tracoAtual[tracoAtual.length - 1];
        lista.forEach(function (e) {
            tracoAtual.push(coordenadas(e));
        });
        ctx.beginPath();
        ctx.moveTo(anterior.x, anterior.y);
        for (let i = tracoAtual.length - lista.length; i < tracoAtual.length; i++) {
            ctx.lineTo(tracoAtual[i].x, tracoAtual[i].y);
        }
        ctx.stroke();
    });

    function finalizarTraco(ev) {
        if (ev.pointerId !== ponteiroAtivo) {
            return;
        }
        if (tracoAtual && tracoAtual.length > 0) {
            tracos.push(tracoAtual);
        }
        tracoAtual = null;
        ponteiroAtivo = null;
        redesenhar();
        atualizarEstado();
    }

    canvas.addEventListener("pointerup", finalizarTraco);
    canvas.addEventListener("pointercancel", finalizarTraco);
    canvas.addEventListener("lostpointercapture", finalizarTraco);
    canvas.addEventListener("contextmenu", function (ev) {
        ev.preventDefault();
    });

    btnDesfazer.addEventListener("click", function () {
        tracos.pop();
        redesenhar();
        atualizarEstado();
    });

    btnLimpar.addEventListener("click", function () {
        tracos = [];
        tracoAtual = null;
        redesenhar();
        atualizarEstado();
    });

    // ---------- API ----------

    async function chamarApi(acao, corpo) {
        const opcoes = {
            method: corpo === undefined ? "GET" : "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" }
        };
        if (corpo !== undefined) {
            opcoes.body = JSON.stringify(corpo);
        }
        let resp;
        try {
            resp = await fetch("api.php?acao=" + encodeURIComponent(acao), opcoes);
        } catch (e) {
            throw new Error("Não foi possível falar com o servidor. Tente de novo.");
        }
        let dados = null;
        try {
            dados = await resp.json();
        } catch (e) {
            dados = null;
        }
        if (!resp.ok || dados === null) {
            const erro = dados && typeof dados.erro === "string" ? dados.erro : "Algo deu errado (" + resp.status + ").";
            throw new Error(erro);
        }
        return dados;
    }

    function mostrarMensagem(texto, tipo) {
        mensagem.textContent = texto || "";
        mensagem.classList.remove("erro", "sucesso");
        if (tipo) {
            mensagem.classList.add(tipo);
        }
    }

    function mostrarTexto(texto, vazio) {
        saidaTexto.textContent = texto;
        saidaTexto.classList.toggle("vazio", !!vazio);
    }

    btnReconhecer.addEventListener("click", async function () {
        if (tracos.length === 0 || ocupado) {
            return;
        }
        ocupado = true;
        ultimoId = null;
        btnSalvar.disabled = true;
        btnReconhecer.classList.add("carregando");
        btnReconhecer.textContent = "Reconhecendo…";
        atualizarEstado();
        mostrarMensagem("", null);

        redesenhar();
        const imagem = canvas.toDataURL("image/png");

        try {
            const dados = await chamarApi("reconhecer", { imagem: imagem });
            const texto = typeof dados.texto === "string" ? dados.texto : "";
            if (texto.trim() === "") {
                mostrarTexto("Não consegui ler nada. Tente escrever maior.", true);
            } else {
                mostrarTexto(texto, false);
                ultimoId = dados.id;
                btnSalvar.disabled = false;
            }
        } catch (e) {
            mostrarTexto("Desenhe algo e clique em Reconhecer.", true);
            mostrarMensagem(e.message, "erro");
        } finally {
            ocupado = false;
            btnReconhecer.classList.remove("carregando");
            btnReconhecer.textContent = "Reconhecer";
            atualizarEstado();
        }
    });

    btnSalvar.addEventListener("click", async function () {
        if (!ultimoId) {
            return;
        }
        btnSalvar.disabled = true;
        mostrarMensagem("", null);
        const nome = "desenho-" + Math.floor(Date.now() / 1000) + ".txt";
        try {
            const dados = await chamarApi("salvar", { id: ultimoId, nome: nome });
            mostrarMensagem("Arquivo salvo: " + (dados.nome || nome), "sucesso");
            await carregarArquivos();
        } catch (e) {
            mostrarMensagem(e.message, "erro");
        } finally {
            btnSalvar.disabled = !ultimoId;
        }
    });

    function renderizarArquivos(arquivos) {
        while (listaArquivos.firstChild) {
            listaArquivos.removeChild(listaArquivos.firstChild);
        }
        if (!Array.isArray(arquivos) || arquivos.length === 0) {
            const li = document.createElement("li");
            li.className = "vazio";
            li.textContent = "Nenhum arquivo ainda";
            listaArquivos.appendChild(li);
            return;
        }
        arquivos.forEach(function (arq) {
            if (!arq || typeof arq.nome !== "string" || typeof arq.url !== "string") {
                return;
            }
            const li = document.createElement("li");
            const a = document.createElement("a");
            a.href = arq.url;
            a.target = "_blank";
            a.rel = "noopener";
            a.textContent = arq.nome;
            li.appendChild(a);
            listaArquivos.appendChild(li);
        });
    }

    async function carregarArquivos() {
        try {
            const dados = await chamarApi("listar");
            renderizarArquivos(dados.arquivos);
        } catch (e) {
            renderizarArquivos([]);
        }
    }

    // ---------- Início ----------

    redesenhar();
    atualizarEstado();
    carregarArquivos();
})();
