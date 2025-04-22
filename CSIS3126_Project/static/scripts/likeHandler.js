
document.addEventListener("DOMContentLoaded", () => {
    const likeForms = document.querySelectorAll(".like-form");

    likeForms.forEach( form => {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            const postId = form.dataset.postId;
            const likeCountElement = document.getElementById(`like-count-${postId}`);
            const button = form.querySelector(".like-button");
            const icon = button.querySelector(".material-symbols-outlined");

            try {
                const response = await fetch(`/like/${postId}`, {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest"
                    }
                });

                if (response.ok) {
                    const data = await response.json();

                    // update like count 
                    likeCountElement.innerText = data.new_like_count;

                    // Toggle like class
                    button.classList.toggle("liked");

                    // animation
                    icon.classList.add("animate-like");
                    setTimeout(() => {
                        icon.classList.remove("animate-like");
                    }, 500);
                } else {
                    console.error("error liking post.")
            }
        } catch (error) {
            console.error("network error:", error)
            }
         });
    });
});
