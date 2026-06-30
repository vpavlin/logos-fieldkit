# Local AI (llama.cpp + LFM2.5-230M)

A small language model running **entirely on the Pi**, served at `:8081` (OpenAI-compatible API),
surfaced as the **Local AI** chat at the bottom of the landing page (`server/index.html`).

- The chat POSTs to `http://<host>:8081/v1/chat/completions`. `llama-server` sets CORS
  (`Access-Control-Allow-Origin`), so the page can call `:8081` cross-port directly — no proxy.
- It "knows" about Logos/Basecamp via **context injection**: facts are baked into the chat's
  system prompt (see the `<script>` in `server/index.html`). No fine-tuning. For deeper/more
  reliable answers, add lightweight RAG over `docs/GUIDE.md` later.

## Build + model (on the Pi, arm64)

```bash
sudo apt-get install -y cmake
git clone --depth 1 https://github.com/ggml-org/llama.cpp ~/llama.cpp
cmake -B ~/llama.cpp/build -S ~/llama.cpp -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF
cmake --build ~/llama.cpp/build -j3 --target llama-server
mkdir -p ~/models
wget -O ~/models/LFM2.5-230M-Q8_0.gguf \
  https://huggingface.co/unsloth/LFM2.5-230M-GGUF/resolve/main/LFM2.5-230M-Q8_0.gguf
```

## Service

```bash
cp systemd/logos-llm.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now logos-llm
# test:
curl -s localhost:8081/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"hi"}],"max_tokens":20}'
```
