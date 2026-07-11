function getCookie(name) {

    let cookieValue = null;

    if (
        document.cookie &&
        document.cookie !== ''
    ) {

        const cookies =
            document.cookie.split(';');

        for (let cookie of cookies) {

            cookie = cookie.trim();

            if (
                cookie.startsWith(
                    name + '='
                )
            ) {

                cookieValue =
                    decodeURIComponent(
                        cookie.substring(
                            name.length + 1
                        )
                    );

                break;
            }
        }
    }

    return cookieValue;
}


document.addEventListener(
    'DOMContentLoaded',
    () => {

        const toggleBtn =
            document.getElementById(
                'project-chat-toggle'
            );

        const widget =
            document.getElementById(
                'project-chat-widget'
            );

        const form =
            document.getElementById(
                'project-chat-form'
            );

        const input =
            document.getElementById(
                'project-chat-input'
            );

        const chatBody =
            document.getElementById(
                'project-chat-body'
            );

        const projectSelect =
            document.getElementById(
                'project-chat-project'
            );

        const statusEl =
            document.getElementById(
                'project-chat-status'
            );

        if (
            !toggleBtn ||
            !widget ||
            !form ||
            !input ||
            !chatBody ||
            !projectSelect
        ) {

            return;

        }

        function appendMessage(
            text,
            role
        ) {

            const wrapper =
                document.createElement(
                    'div'
                );

            wrapper.className =
                `chat-msg ${role}`;

            wrapper.textContent =
                text;

            chatBody.appendChild(
                wrapper
            );

            chatBody.scrollTop =
                chatBody.scrollHeight;
        }

        function setStatus(
            text,
            isError = false
        ) {

            if (!statusEl)
                return;

            statusEl.textContent =
                text;

            statusEl.style.color =
                isError
                    ? '#fb7185'
                    : '#cbd5e1';
        }

        toggleBtn.addEventListener(
            'click',
            () => {

                const isOpen =
                    widget.getAttribute(
                        'data-open'
                    ) === 'true';

                widget.setAttribute(
                    'data-open',
                    (!isOpen).toString()
                );

                widget.style.display =
                    !isOpen
                        ? 'flex'
                        : 'none';

                if (!isOpen)
                    setStatus('');
            }
        );

        form.addEventListener(
            'submit',
            async (e) => {

                e.preventDefault();

                const projectId =
                    projectSelect.value;

                const question =
                    (
                        input.value || ''
                    ).trim();

                if (!projectId) {

                    setStatus(
                        'Select a project first.',
                        true
                    );

                    return;
                }

                if (!question)
                    return;

                appendMessage(
                    question,
                    'user'
                );

                input.value = '';

                setStatus(
                    'Thinking...'
                );

                try {

                    const response =
                        await fetch(

                            `/chat-api/${projectId}/`,

                            {

                                method:
                                    'POST',

                                headers: {

                                    'Content-Type':
                                        'application/json',

                                    'X-CSRFToken':
                                        getCookie(
                                            'csrftoken'
                                        )

                                },

                                body:
                                    JSON.stringify({

                                        question:
                                            question

                                    })

                            }

                        );

                    if (
                        !response.ok
                    ) {

                        const data =
                            await response
                                .json()
                                .catch(
                                    () => ({})
                                );

                        throw new Error(

                            data.error ||

                            `Request failed (${response.status})`

                        );
                    }

                    const data =
                        await response.json();

                    appendMessage(

                        data.answer ||
                        'No answer generated.',

                        'assistant'

                    );

                    setStatus('');

                }

                catch (error) {

                    console.error(
                        error
                    );

                    appendMessage(

                        error.message ||

                        'Chat request failed.',

                        'assistant'

                    );

                    setStatus(

                        error.message ||

                        'Chat request failed.',

                        true

                    );
                }
            }
        );
    }
);