import { GoogleGenAI } from "https://esm.run/@google/genai";

// Ambil elemen dari DOM
const apiKeyInput = document.getElementById("apiKey");
const saveKeyBtn = document.getElementById("saveKeyBtn");
const systemInstructionInput = document.getElementById("systemInstruction");
const storyMemoryInput = document.getElementById("storyMemory");
const storyBox = document.getElementById("storyBox");
const generateBtn = document.getElementById("generateBtn");
const statusIndicator = document.getElementById("statusIndicator");

// Load API Key dari localStorage jika ada
window.addEventListener("DOMContentLoaded", () => {
    const savedKey = localStorage.getItem("gemini_api_key");
    if (savedKey) {
        apiKeyInput.value = savedKey;
    }
});

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

// Fungsi Utama Generate Cerita
generateBtn.addEventListener("click", async () => {
    const apiKey = apiKeyInput.value.trim() || localStorage.getItem("gemini_api_key");
    
    if (!apiKey) {
        alert("Harap masukkan dan simpan Gemini API Key terlebih dahulu di sidebar!");
        return;
    }

    const currentText = storyBox.value;
    const systemInstruction = systemInstructionInput.value;
    const memory = storyMemoryInput.value;

    if (!currentText.trim()) {
        alert("Tuliskan beberapa kalimat awal cerita terlebih dahulu!");
        return;
    }

    // Ubah status jadi 'Menulis...'
    statusIndicator.textContent = "AI sedang menulis...";
    statusIndicator.style.color = "#ff9800";
    generateBtn.disabled = true;

    try {
        const ai = new GoogleGenAI({ apiKey: apiKey });

        // Gabungkan memori/lore dengan teks cerita saat ini sebagai konteks
        let fullPrompt = "";
        if (memory.trim()) {
            fullPrompt += `[Konteks & Memori Cerita]:\n${memory}\n\n`;
        }
        fullPrompt += `[Teks Cerita Saat Ini]:\n${currentText}\n\n[Instruksi]: Lanjutkan paragraf cerita di atas secara natural, imersif, dan nyambung.`;

        const response = await ai.models.generateContent({
            model: "gemini-2.5-flash",
            contents: fullPrompt,
            config: {
                systemInstruction: systemInstruction,
                temperature: 0.85,
            }
        });

        // Tambahkan hasil generasi ke dalam kotak teks (dengan spasi/baris baru yang rapi)
        const generatedText = response.text;
        storyBox.value = currentText + (currentText.endsWith("\n") ? "" : "\n") + generatedText;
        
        statusIndicator.textContent = "Siap";
        statusIndicator.style.color = "#4caf50";
    } catch (error) {
        console.error(error);
        statusIndicator.textContent = "Error!";
        statusIndicator.style.color = "#f44336";
        alert("Terjadi kesalahan saat memanggil Gemini API. Periksa kembali API Key Anda.");
    } finally {
        generateBtn.disabled = false;
    }
});
