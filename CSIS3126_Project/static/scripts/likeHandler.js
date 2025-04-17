// Like Button handling for liking a post and animating the like count 
document.addEventListener("DOMContentLoaded", function () {
    const likeButtons = document.querySelectorAll(".like-button");

    likeButtons.forEach(button => {
        button.addEventListener("click", function (event) {
            event.preventDefault(); 
            
            const form = button.closest("form");
            const postCard = button.closest(".post-card");
            const likeCountElement = postCard.querySelector(".like-count");

            if (form && likeCountElement) {
                const formData = new FormData(form);
                const postId = form.action.split("/").pop();

                fetch(form.action, {
                    method: "POST",
                    body: formData,
                })
                .then(response => response.json())
                .then(data => {
                    // Update llike count with animation
                    if (data.likes !== undefined) {
                    let newLikes = data.likes;

                    likeCountElement.classList.add('animating');
                    likeCountElement.innerText = newLikes;

                    button.classList.toggle("liked");

                    setTimeout(() => {
                        likeCountElement.classList.remove("animating");
                    }, 500);
                }
            })
                .catch(error => {
                    console.error("like failed:", error);
                });
            }
        });
    });
});