(function () {
    document.addEventListener("click", function (event) {
        var actions = event.target.closest(".block-card__actions");
        if (!actions) return;

        var button = event.target.closest("button");
        if (!button) return;

        var form = button.closest("form");
        if (!form) return;

        event.preventDefault();
        form.requestSubmit(button);
    });
})();
