(function () {
    const btn = document.createElement("div");
    btn.innerHTML = "💬";
    btn.style.position = "fixed";
    btn.style.bottom = "20px";
    btn.style.right = "20px";
    btn.style.width = "60px";
    btn.style.height = "60px";
    btn.style.borderRadius = "50%";
    btn.style.background = "#0084ff";
    btn.style.color = "white";
    btn.style.display = "flex";
    btn.style.justifyContent = "center";
    btn.style.alignItems = "center";
    btn.style.cursor = "pointer";
    btn.style.zIndex = "99999";
    document.body.appendChild(btn);

    const box = document.createElement("div");
    box.style.position = "fixed";
    box.style.bottom = "100px";
    box.style.right = "20px";
    box.style.width = "300px";
    box.style.height = "400px";
    box.style.background = "white";
    box.style.border = "1px solid #ccc";
    box.style.borderRadius = "10px";
    box.style.display = "none";
    box.style.flexDirection = "column";
    box.style.zIndex = "99999";
    document.body.appendChild(box);

    const chat = document.createElement("div");
    chat.style.flex = "1";
    chat.style.padding = "10px";
    chat.style.overflowY = "auto";
    box.appendChild(chat);

    const input = document.createElement("input");
    input.placeholder = "Ваш вопрос...";
    input.style.border = "none";
    input.style.borderTop = "1px solid #ccc";
    input.style.padding = "10px";
    input.style.width = "100%";
    box.appendChild(input);

    btn.onclick = () => {
        box.style.display = box.style.display === "none" ? "flex" : "none";
    };

    input.addEventListener("keypress", async (e) => {
        if (e.key === "Enter" && input.value.trim()) {
            const message = input.value.trim();
            chat.innerHTML += `<div><b>Вы:</b> ${message}</div>`;
            input.value = "";

            const API_URL = "https://fortis-chatbot.onrender.com/chat";
            const res = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message })
            });

            const data = await res.json();
            chat.innerHTML += `<div><b>Бот:</b> ${data.reply}</div>`;
            chat.scrollTop = chat.scrollHeight;
        }
    });
})();

