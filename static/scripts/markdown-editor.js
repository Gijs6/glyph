(function () {
    if (window.glyphMarkdownEditor) return;
    window.glyphMarkdownEditor = true;

    function button(name, action, text) {
        return { name: name, action: action, text: text, title: text, className: "btn btn--sm" };
    }

    function toolbar() {
        return [button("bold", EasyMDE.toggleBold, "Bold"), button("italic", EasyMDE.toggleItalic, "Italic"), button("heading", EasyMDE.toggleHeadingSmaller, "Heading"), button("quote", EasyMDE.toggleBlockquote, "Quote"), button("unordered-list", EasyMDE.toggleUnorderedList, "Bulleted list"), button("ordered-list", EasyMDE.toggleOrderedList, "Numbered list"), button("link", EasyMDE.drawLink, "Link"), button("image", EasyMDE.drawImage, "Image"), Object.assign(button("preview", EasyMDE.togglePreview, "Preview"), { noDisable: true }), Object.assign(button("side-by-side", EasyMDE.toggleSideBySide, "Side by side"), { noDisable: true, noMobile: true }), Object.assign(button("fullscreen", EasyMDE.toggleFullScreen, "Full screen"), { noDisable: true, noMobile: true }), { name: "guide", action: "https://www.markdownguide.org/basic-syntax/", text: "Markdown guide", title: "Markdown guide", className: "btn btn--sm", noDisable: true }];
    }

    function enhance(root) {
        root.querySelectorAll("textarea[data-markdown-editor]:not([data-markdown-editor-ready])").forEach(function (textarea) {
            textarea.setAttribute("data-markdown-editor-ready", "true");

            var mde = new EasyMDE({
                element: textarea,
                spellChecker: false,
                autoDownloadFontAwesome: false,
                forceSync: true,
                toolbar: toolbar(),
                placeholder: textarea.getAttribute("placeholder") || ""
            });

            mde.codemirror.on("change", function () {
                textarea.dispatchEvent(new Event("input", { bubbles: true }));
            });
        });
    }

    enhance(document);
    document.body.addEventListener("htmx:afterSwap", function (event) {
        enhance(event.detail.target);
    });
})();
