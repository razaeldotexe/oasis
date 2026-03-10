# 💡 Project Idea: Modular Discord Embed Sender

## 🎯 Objective
Membuat sistem pengirim pesan Discord (**Sender**) yang terpisah dari core bot utama (`bot.py`). Sistem ini bersifat *stateless* dan berjalan via CLI (Command Line Interface) untuk mengirim pesan *rich embed* berdasarkan konten file lokal.

## 🛠️ Tech Stack
*   **Language:** Python
*   **Library:** `aiohttp` (untuk request async), `discord.py` (untuk utilitas Webhook & Embed)
*   **Method:** Discord Webhooks (lebih ringan daripada WebSocket bot login)
*   **Environment:** `.env` untuk menyimpan Webhook URL

## ⚙️ Architecture Flow

```mermaid
graph LR
    A[File Input\n(.json, .py, .txt)] --> B[Sender Script\n(sender.py)];
    B --> C{Detect Extension};
    C -- .json --> D[Parse as Embed Object];
    C -- .txt/.md --> E[Parse as Description];
    C -- .py/.js/.html --> F[Format as Code Block];
    D & E & F --> G[Construct Payload];
    G --> H[POST to Discord Webhook];
    H --> I[Discord Channel];
