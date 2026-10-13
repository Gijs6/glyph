(function () {
    if (window.glyphBlockActions) return;
    window.glyphBlockActions = true;

    function syncMoveButtons() {
        var cards = document.querySelectorAll("#block-builder .block-card");
        cards.forEach(function (card, index) {
            var up = card.querySelector('input[name="direction"][value="up"]');
            var down = card.querySelector('input[name="direction"][value="down"]');
            if (up) up.form.querySelector("button").disabled = index === 0;
            if (down) down.form.querySelector("button").disabled = index === cards.length - 1;
        });
    }

    document.addEventListener("htmx:afterSettle", syncMoveButtons);

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
