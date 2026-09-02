# 🏦 Personal Finance AI Assistant Bot

Asisten keuangan pribadi berbasis AI yang mencatat transaksi keuangan secara otomatis ke Google Sheets melalui chat Telegram dengan bahasa natural.

---

## 🚀 Panduan Menjalankan Bot di VS Code

Berikut adalah langkah-langkah untuk membuka, menyiapkan, dan menjalankan kembali bot ini dari VS Code.

### Langkah 1: Buka Project di VS Code
1. Buka aplikasi **VS Code**.
2. Klik menu **File** -> **Open Folder...**
3. Pilih folder project ini: `Personal Finance AI Assistant`

### Langkah 2: Buka Terminal di VS Code
1. Buka terminal internal VS Code dengan menekan tombol shortkey:
   - `Ctrl` + `~` (backtick)
   - Atau melalui menu bar atas: **Terminal** -> **New Terminal**

---

### Langkah 3: Pilih Metode Menjalankan Bot

Anda bisa memilih salah satu dari dua metode di bawah ini:

#### Pilihan A: Menggunakan Virtual Environment (Sangat Direkomendasikan 🌟)
Metode ini memastikan library Python tidak bentrok dengan project lain di komputer Anda.

1. **Buat Virtual Environment (Hanya perlu dilakukan sekali di awal):**
   ```bash
   python -m venv .venv
   ```
2. **Aktifkan Virtual Environment:**
   * Jika menggunakan **PowerShell** (Default VS Code Windows):
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   * Jika menggunakan **Command Prompt (CMD)**:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   *(Tanda `.venv` berwarna hijau akan muncul di sebelah kiri baris terminal Anda jika aktif)*

3. **Install Dependencies/Library (Hanya perlu sekali setelah membuat venv):**
   ```bash
   pip install -r requirements.txt
   ```

4. **Jalankan Bot:**
   ```bash
   python main.py
   ```

---

#### Pilihan B: Menggunakan Python Global (Lebih Instan)
Jika Anda tidak ingin menggunakan virtual environment dan ingin langsung menjalankan bot secara global:

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Jalankan Bot:**
   ```bash
   python main.py
   ```

---

## 🛑 Cara Menghentikan Bot
Untuk mematikan engine bot di terminal, cukup tekan tombol:
`Ctrl` + `C` di dalam terminal VS Code Anda.

---

## 📂 Struktur Penting Lainnya
* `.env` : File konfigurasi token bot, API Key Gemini, dan ID Google Sheets. Jangan pernah menghapus file ini.
* `credentials.json` : File kredensial akses API Google Sheets Anda. Jangan pernah membagikan atau menghapus file ini.
* `/tests` : Kumpulan unit-test untuk menguji integritas pencatatan keuangan. Untuk mengetes: `python -m pytest tests/`
