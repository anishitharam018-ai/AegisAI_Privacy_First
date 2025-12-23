document
  .getElementById("analyze-btn")
  .addEventListener("click", async function () {
    const inputText = document.getElementById("user-input").value;
    if (!inputText.trim()) {
      alert("Please enter a message.");
      return;
    }

    const btn = document.getElementById("analyze-btn");
    const originalText = btn.textContent;
    btn.textContent = "Analyzing...";
    btn.disabled = true;

    try {
      const response = await fetch("/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: inputText }), // ✅ key matches Flask
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();

      // Update User View
      document.getElementById("original-text").textContent = data.user_view; // ✅ matches Flask key

      // Update AI View (Masked) with highlighting
      const maskedHtml = data.ai_view.replace(
        /\[MASKED_[^\]]+\]/g,
        '<span class="masked">$&</span>'
      );
      document.getElementById("masked-text").innerHTML = maskedHtml; // ✅ matches Flask key

      // Update Detected Sensitive Data
      const list = document.getElementById("sensitive-list");
      list.innerHTML = "";
      if (data.detected_sensitive_data.length > 0) {
        // ✅ matches Flask key
        data.detected_sensitive_data.forEach((item) => {
          const li = document.createElement("li");
          li.textContent = item;
          list.appendChild(li);
        });
      } else {
        const li = document.createElement("li");
        li.textContent = "No sensitive data detected.";
        list.appendChild(li);
      }

      // Update AI Analysis Result
      document.getElementById("analysis-json").textContent = JSON.stringify(
        data.analysis, // ✅ matches Flask key
        null,
        2
      );
    } catch (error) {
      console.error("Error:", error);
      alert("An error occurred while analyzing the message. Please try again.");
    } finally {
      btn.textContent = originalText;
      btn.disabled = false;
    }
  });
