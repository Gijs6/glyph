(function () {
    if (window.glyphCopyLink) return;
    window.glyphCopyLink = true;

    document.addEventListener("click", function (event) {
        var button = event.target.closest("[data-copy-target]");
        if (!button) return;

        var input = document.getElementById(button.getAttribute("data-copy-target"));
        if (!input) return;

        navigator.clipboard.writeText(input.value).then(
            function () {
                window.toast("Link copied.", { type: "success" });
            },
            function () {
                input.select();
                window.toast("Couldn't copy the link. Copy it from the field instead.", { type: "danger" });
            }
        );
    });
})();
