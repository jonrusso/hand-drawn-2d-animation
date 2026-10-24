<div align="center">

# hand-drawn-2d-animation

[English](README.md) | **Português (Brasil)**

![Animatic a lápis ao lado do filme final](docs/images/pencil-to-final.gif)

</div>

> Entra uma frase, sai um curta 2D com cara de desenhado à mão. Entrevista da história, fichas de personagem, storyboard, um prompt mestre, **uma geração** no CapCut com o Seedance, QA, e um animatic a lápis feito com ferramentas open source.

## Instalar
Entregue o link para o seu agente:

```text
Instale esta skill para mim: https://github.com/jonrusso/hand-drawn-2d-animation
```

O agente segue o [INSTALL_FOR_AGENTS.md](INSTALL_FOR_AGENTS.md). Ou instale você mesmo:

```bash
npx skills add jonrusso/hand-drawn-2d-animation
```
```text
/plugin marketplace add jonrusso/hand-drawn-2d-animation         # Claude Code
/plugin install hand-drawn-2d-animation@hand-drawn-2d-animation
```
Manual: copie `skills/hand-drawn-2d-animation` para `~/.claude/skills/` (Claude Code) ou `~/.agents/skills/` (Codex).

Depois diga:
> Use a skill hand-drawn-2d-animation. Me entreviste sobre a minha ideia de história, monte a bíblia, o storyboard e o prompt mestre, e me pergunte antes de gastar créditos.

A skill e os guias são em inglês de propósito: é a língua em que os agentes e os geradores de vídeo trabalham melhor. Pode conversar com o agente em português normalmente.

## Por quê
Um modelo de vídeo com IA é uma máquina de probabilidade. A maior parte da animação ruim feita com IA não é geração ruim; é um chute que o modelo teve que dar porque ninguém decidiu o que a mão segura, por que o rosto muda ou o que faz o corte. Esta skill tira esses chutes em etapas baratas e gasta crédito de vídeo uma vez só.

## Como funciona
```
entrevista ─▶ bíblia ─▶ planos + storyboard ─▶ prompt mestre ─▶ UMA geração ─▶ QA + reparo local ─▶ 1080p
  grátis       imagens    imagens + animatic     grátis, conferido  crédito de vídeo  só os reparos
```

O que os scripts conferem antes de qualquer gasto (`master_prompt.py check`): cinco dedos escritos por extenso em toda mão, uma causa para toda mudança de rosto, um motivo para todo corte, nenhum enquadramento repetido em sequência, nenhuma quebra de direção de tela, nenhuma palavra que transforme água desenhada em vidro, nenhum nome de filme ou estúdio, e o limite de caracteres do prompt.

O caso completo, com custos e todos os erros que aconteceram: [examples/bolhao/CASE_STUDY.md](examples/bolhao/CASE_STUDY.md).

## Agradecimentos
O visual desta skill foi estudado a partir da obra de **Tyrus Wong**, cujas florestas pintadas definiram o visual de *Bambi* (1942), da Walt Disney Animation Studios, e dos fundos pintados à mão de *Branca de Neve e os Sete Anões* (1937), da Disney. Eles estão creditados aqui porque é de onde vem esse estilo. Nenhum quadro, personagem ou nome entra nos prompts, e este projeto não tem vínculo nem aval da Disney.

Feito com CapCut, o plugin do ChatGPT, Codex e Seedance, e com open source: Video Depth Anything (Small, Apache 2.0), Anime2Sketch (MIT), anime-segmentation / isnet-anime (Apache 2.0), PyTorch, ONNX Runtime, OpenCV, FFmpeg, Pillow, NumPy.

Feito por [@russodev](https://instagram.com/russodev), com Claude Code e Codex.

## Licença
Código: [Apache 2.0](LICENSE). Textos, prompts e imagens de exemplo: [CC BY 4.0](LICENSE-docs).
