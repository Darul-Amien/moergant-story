import { GoogleGenAI } from "https://esm.run/@google/genai";

// Nama model Gemini (ganti di sini saja jika Google mengubah nama model lagi)
const MODEL_NAME = "gemini-3.8-flash";

// Ambil elemen dari DOM
const apiKeyInput = document.getElementById("apiKey");
const saveKeyBtn = document.getElementById("saveKeyBtn");
const systemInstructionInput = document.getElementById("systemInstruction");
const storyMemoryInput = document.getElementById("storyMemory");
const storyTitleInput = document.getElementById("storyTitle");
const storyBox = document.getElementById("storyBox");
const generateBtn = document.getElementById("generateBtn");
const retryBtn = document.getElementById("retryBtn");
const newStoryBtn = document.getElementById("newStoryBtn");
const statusIndicator = document.getElementById("statusIndicator");

// Menyimpan teks cerita sebelum generate terakhir (dipakai oleh tombol Retry)
let lastBaseText = null;

// ===== Simpan & pulihkan data otomatis =====
const STORAGE_KEY = "cerita_ai_data";

function saveAll() {
    try {
        const data = {
            title: storyTitleInput.value,
            story: storyBox.value,
            system: systemInstructionInput.value,
            memory: storyMemoryInput.value,
            lastBaseText: lastBaseText
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (e) {
        console.error("Gagal menyimpan data:", e);
    }
}

function loadAll() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return;
        const data = JSON.parse(raw);
        if (data.title !== undefined) storyTitleInput.value = data.title;
        if (data.story !== undefined) storyBox.value = data.story;
        if (data.system !== undefined) systemInstructionInput.value = data.system;
        if (data.memory !== undefined) storyMemoryInput.value = data.memory;
        if (data.lastBaseText !== undefined) lastBaseText = data.lastBaseText;
    } catch (e) {
        console.error("Gagal memuat data:", e);
    }
}

// Simpan setiap kali ada perubahan ketikan
[storyTitleInput, storyBox, systemInstructionInput, storyMemoryInput].forEach(el => {
    el.addEventListener("input", saveAll);
});

// Simpan juga saat tab disembunyikan / ditutup (penting di HP)
document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") saveAll();
});
window.addEventListener("pagehide", saveAll);

// Load data saat halaman dibuka
// (script type="module" sudah dijalankan setelah DOM siap, jadi bisa langsung dipanggil)
const savedKey = localStorage.getItem("gemini_api_key");
if (savedKey) {
    apiKeyInput.value = savedKey;
}
loadAll();

// Simpan API Key ke localStorage
saveKeyBtn.addEventListener("click", () => {
    const key = apiKeyInput.value.trim();
    if (key) {
        localStorage.setItem("gemini_api_key", key);
        alert("API Key berhasil disimpan di browser Anda!");
    } else {
        alert("Mohon masukkan API Key yang valid.");
    }
});

// Atur status & tombol saat AI bekerja / selesai
function setBusy(isBusy) {
    generateBtn.disabled = isBusy;
    retryBtn.disabled = isBusy;
    newStoryBtn.disabled = isBusy;

    if (isBusy) {
        statusIndicator.textContent = "AI sedang menulis...";
        statusIndicator.style.color = "#ff9800";
    }
}

// Fungsi inti: kirim teks dasar ke Gemini lalu tambahkan hasilnya ke editor
async function generateStory(baseText) {
    const apiKey = apiKeyInput.value.trim() || localStorage.getItem("gemini_api_key");

    if (!apiKey) {
        alert("Harap masukkan dan simpan Gemini API Key terlebih dahulu di sidebar!");
        return;
    }

    if (!baseText.trim()) {
        alert("Tuliskan beberapa kalimat awal cerita terlebih dahulu!");
        return;
    }

    const systemInstruction = systemInstructionInput.value;
    const memory = storyMemoryInput.value;

    // Simpan teks dasar agar bisa di-retry
    lastBaseText = baseText;

    setBusy(true);

    try {
        const ai = new GoogleGenAI({ apiKey: apiKey });

        // Gabungkan memori/lore dengan teks cerita saat ini sebagai konteks
        let fullPrompt = "";
        if (memory.trim()) {
            fullPrompt += `[Konteks & Memori Cerita]:\n${memory}\n\n`;
        }
        fullPrompt += `[Teks Cerita Saat Ini]:\n${baseText}\n\n[Instruksi]: Lanjutkan paragraf cerita di atas secara natural, imersif, dan nyambung.`;

        const response = await ai.models.generateContent({
            model: MODEL_NAME,
            contents: fullPrompt,
            config: {
                systemInstruction: systemInstruction,
                temperature: 0.85,
            }
        });

        // Pastikan balasan tidak kosong (bisa kosong jika diblokir filter keamanan)
        const generatedText = response.text;
        if (!generatedText) {
            throw new Error("Balasan kosong. Kemungkinan diblokir filter keamanan Gemini. Coba ubah alur cerita atau ulangi.");
        }

        // Tambahkan hasil generasi ke dalam kotak teks (dengan baris baru yang rapi)
        storyBox.value = baseText + (baseText.endsWith("\n") ? "" : "\n") + generatedText;

        // Scroll otomatis ke bagian paling bawah
        storyBox.scrollTop = storyBox.scrollHeight;

        // Simpan hasil dari AI
        saveAll();

        statusIndicator.textContent = "Siap";
        statusIndicator.style.color = "#4caf50";
    } catch (error) {
        console.error(error);
        // Simpan lastBaseText meski gagal, supaya Retry tetap bisa dipakai setelah refresh
        saveAll();
        statusIndicator.textContent = "Error!";
        statusIndicator.style.color = "#f44336";

        const detail = (error && error.message) ? error.message : String(error);
        let petunjuk = "";

        if (/API key not valid|API_KEY_INVALID|\b400\b/i.test(detail)) {
            petunjuk = "API Key tidak valid. Cek lagi key-nya dan pastikan tidak ada spasi.";
        } else if (/\b403\b|PERMISSION_DENIED|referrer/i.test(detail)) {
            petunjuk = "Akses ditolak. Cek pembatasan domain pada API Key atau apakah Gemini API aktif.";
        } else if (/\b404\b|not found/i.test(detail)) {
            petunjuk = "Model tidak ditemukan. Ganti nilai MODEL_NAME di bagian atas script.js.";
        } else if (/\b429\b|RESOURCE_EXHAUSTED|quota/i.test(detail)) {
            petunjuk = "Kuota atau batas permintaan habis. Tunggu sebentar lalu coba lagi.";
        } else if (/\b503\b|overloaded|UNAVAILABLE/i.test(detail)) {
            petunjuk = "Server Gemini sedang sibuk. Coba lagi beberapa saat.";
        } else if (/Failed to fetch|NetworkError/i.test(detail)) {
            petunjuk = "Koneksi internet bermasalah atau permintaan diblokir.";
        }

        alert("Terjadi kesalahan saat memanggil Gemini API.\n\n" + (petunjuk ? petunjuk + "\n\n" : "") + "Detail: " + detail);
    } finally {
        setBusy(false);
    }
}

// Tombol Lanjutkan Cerita (Generate)
generateBtn.addEventListener("click", () => {
    generateStory(storyBox.value);
});

// Tombol Ulangi (Retry): buang hasil generate terakhir, lalu generate ulang
retryBtn.addEventListener("click", () => {
    if (lastBaseText === null) {
        alert("Belum ada generate sebelumnya yang bisa diulang.");
        return;
    }
    storyBox.value = lastBaseText;
    generateStory(lastBaseText);
});

// Tombol Cerita Baru (Reset)
newStoryBtn.addEventListener("click", () => {
    if (!confirm("Yakin ingin memulai cerita baru? Semua teks di editor akan dihapus.")) {
        return;
    }

    storyBox.value = "";
    storyTitleInput.value = "Cerita Fiksi Baru";
    lastBaseText = null;

    // Hapus baris di bawah ini jika ingin memori/lore ikut dikosongkan saat reset:
    // storyMemoryInput.value = "";

    saveAll();

    statusIndicator.textContent = "Siap";
    statusIndicator.style.color = "#4caf50";
});
