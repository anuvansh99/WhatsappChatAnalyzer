let globalData = null;
let expandStates = {};

// Loader with animation and message
function showLoader(show) {
    const loader = document.getElementById('loader');
    if (show) {
        loader.classList.remove('hidden');
    } else {
        loader.classList.add('hidden');
    }
}

function showResults(show) {
    const results = document.getElementById('results');
    results.classList.toggle('hidden', !show);
    if (show) {
        results.classList.add('animate__fadeInUp');
    } else {
        results.classList.remove('animate__fadeInUp');
    }
}

function showUserSelect(show) {
    const section = document.getElementById('user-select-section');
    section.classList.toggle('hidden', !show);
    if (show) {
        section.classList.add('animate__fadeIn');
    } else {
        section.classList.remove('animate__fadeIn');
    }
}

function showMostBusyUsers(show) {
    document.getElementById('most-busy-users-section').classList.toggle('hidden', !show);
}

function fillStats(stats) {
    document.getElementById('stat-messages').textContent = stats.num_messages;
    document.getElementById('stat-words').textContent = stats.words;
    document.getElementById('stat-media').textContent = stats.num_media_messages;
    document.getElementById('stat-links').textContent = stats.num_links;
}

function setImage(id, base64) {
    const img = document.getElementById(id);
    if (img && base64) {
        img.src = "data:image/png;base64," + base64;
        img.classList.remove('hidden');
        img.classList.add('animate__animated', 'animate__fadeIn');
    } else if (img) {
        img.classList.add('hidden');
    }
}

function fillTableWithExpand(tableId, rows, headers) {
    const table = document.getElementById(tableId);
    if (!rows || rows.length === 0) {
        table.innerHTML = "<tr><td>No data available</td></tr>";
        return;
    }

    let displayRows = rows;
    let isExpanded = expandStates[tableId] || false;

    if (!isExpanded && rows.length > 10) {
        displayRows = rows.slice(0, 10);
    }

    let html = "";
    // Generate headers
    if (headers && headers.length) {
        html += "<tr>";
        headers.forEach(h => html += `<th>${h}</th>`);
        html += "</tr>";
    } else if (displayRows.length > 0 && typeof displayRows[0] === 'object') {
        html += "<tr>";
        Object.keys(displayRows[0]).forEach(h => html += `<th>${h}</th>`);
        html += "</tr>";
    }

    // Generate rows
    displayRows.forEach(row => {
        html += "<tr>";
        if (Array.isArray(row)) {
            row.forEach(cell => html += `<td>${cell}</td>`);
        } else if (typeof row === 'object') {
            Object.values(row).forEach(cell => html += `<td>${cell}</td>`);
        }
        html += "</tr>";
    });

    table.innerHTML = html;

    // Expand/collapse controls
    const containerId = tableId + "-container";
    let container = document.getElementById(containerId);
    if (!container) {
        container = document.createElement('div');
        container.id = containerId;
        container.className = 'table-controls';
        table.parentNode.insertBefore(container, table.nextSibling);
    }

    if (rows.length > 10) {
        container.innerHTML = `<button class="expand-btn btn btn-sm btn-outline-info" id='${tableId}-expand-btn'>${
            isExpanded ? '▲ Collapse' : '▼ Expand'
        }</button>`;
        document.getElementById(`${tableId}-expand-btn`).addEventListener('click', () => {
            expandStates[tableId] = !expandStates[tableId];
            fillTableWithExpand(tableId, rows, headers);
        });
    } else {
        container.innerHTML = '';
    }
}

function fillTaglines(taglines) {
    const list = document.getElementById('taglines-list');
    list.innerHTML = "";
    for (const [user, tagline] of Object.entries(taglines)) {
        const li = document.createElement('li');
        li.innerHTML = `<strong>${user}:</strong> ${tagline}`;
        list.appendChild(li);
    }
}

function fillSummary(summary) {
    document.getElementById('summary').textContent = summary;
}

function populateUserDropdown(users) {
    const select = document.getElementById('user-select');
    select.innerHTML = "";
    users.forEach(user => {
        const opt = document.createElement('option');
        opt.value = user;
        opt.textContent = user;
        select.appendChild(opt);
    });
}

function renderComponentsIncrementally(data, selectedUser) {
    showResults(true);

    fillStats(data.stats);
    setImage('monthly-timeline', data.plots.monthly_timeline);

    const renderingPhases = [
        { delay: 300, action: () => setImage('daily-timeline', data.plots.daily_timeline) },
        { delay: 600, action: () => {
            setImage('busy-day', data.plots.busy_day);
            setImage('busy-month', data.plots.busy_month);
        }},
        { delay: 900, action: () => setImage('heatmap', data.plots.heatmap) },
        { delay: 1200, action: () => setImage('wordcloud', data.plots.wordcloud) },
        { delay: 1400, action: () => setImage('common-words-bar', data.plots.common_words_bar) },
        { delay: 1500, action: () => setImage('emoji-pie', data.plots.emoji_pie) },
        { delay: 1600, action: () => {
            if (selectedUser === "Overall" && data.most_busy_users_df) {
                showMostBusyUsers(true);
                setImage('most-busy-users', data.plots.most_busy_users);
                fillTableWithExpand(
                    'most-busy-users-table', 
                    data.most_busy_users_df,
                    data.most_busy_users_df?.[0] ? Object.keys(data.most_busy_users_df[0]) : []
                );
            } else {
                showMostBusyUsers(false);
            }
        }},
        { delay: 1800, action: () => {
            fillSummary(data.summary);
            fillTaglines(data.taglines);
        }}
    ];

    renderingPhases.forEach(({ delay, action }) => setTimeout(action, delay));
}

document.getElementById('upload-form').addEventListener('submit', function(e) {
    e.preventDefault();
    showLoader(true);
    showResults(false);
    showUserSelect(false);
    document.getElementById('quiz-section').classList.add('hidden');

    const fileInput = document.getElementById('chat-file');
    const file = fileInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    fetch('/analyze', {
        method: 'POST',
        body: formData
    })
    .then(async response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        globalData = data;
        populateUserDropdown(data.users);
        showUserSelect(true);
        renderComponentsIncrementally(data, "Overall");
    })
    .catch(err => {
        console.error('Analysis error:', err);
        alert("Error analyzing file. Please check the file format and try again.");
    })
    .finally(() => {
        showLoader(false);
    });
});

document.getElementById('analyze-user').addEventListener('click', function() {
    if (!globalData) return;
    showLoader(true);
    showResults(false);
    document.getElementById('quiz-section').classList.add('hidden');

    const selectedUser = document.getElementById('user-select').value;
    const fileInput = document.getElementById('chat-file');
    const file = fileInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('selected_user', selectedUser);

    fetch('/analyze', {
        method: 'POST',
        body: formData
    })
    .then(async response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        globalData = data;
        renderComponentsIncrementally(data, selectedUser);
    })
    .catch(err => {
        console.error('User analysis error:', err);
        alert("Error analyzing user data. Please try again.");
    })
    .finally(() => {
        showLoader(false);
    });
});

// ================== QUIZ FEATURE ==================

document.getElementById('create-quiz-btn').addEventListener('click', function() {
    const fileInput = document.getElementById('chat-file');
    const file = fileInput.files[0];
    if (!file) {
        alert("Please select a WhatsApp chat .txt file first.");
        return;
    }

    showLoader(true);
    showResults(false);
    showUserSelect(false);
    document.getElementById('quiz-section').classList.add('hidden');

    const formData = new FormData();
    formData.append('file', file);

    fetch('/quiz', {
        method: 'POST',
        body: formData
    })
    .then(async response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        renderQuiz(data.quiz);
    })
    .catch(err => {
        alert("Error creating quiz. Please try again.");
        console.error(err);
    })
    .finally(() => {
        showLoader(false);
    });
});

function renderQuiz(quizQuestions) {
    const quizSection = document.getElementById('quiz-section');
    quizSection.innerHTML = '';
    quizSection.classList.remove('hidden');

    if (!quizQuestions || quizQuestions.length === 0) {
        quizSection.innerHTML = '<div class="alert alert-warning">No quiz questions could be generated from this chat.</div>';
        return;
    }

    // Build the quiz form
    const form = document.createElement('form');
    form.id = 'quiz-form';
    form.className = 'quiz-form bg-dark text-light p-4 rounded shadow';

    quizQuestions.forEach((q, idx) => {
        const qDiv = document.createElement('div');
        qDiv.className = 'mb-4';

        const qLabel = document.createElement('label');
        qLabel.className = 'form-label fw-bold';
        qLabel.textContent = `Q${idx + 1}. ${q.question}`;
        qDiv.appendChild(qLabel);

        q.options.forEach((option, oidx) => {
            const optDiv = document.createElement('div');
            optDiv.className = 'form-check';

            const optInput = document.createElement('input');
            optInput.className = 'form-check-input';
            optInput.type = 'radio';
            optInput.name = `q${idx}`;
            optInput.id = `q${idx}-opt${oidx}`;
            optInput.value = option;

            const optLabel = document.createElement('label');
            optLabel.className = 'form-check-label';
            optLabel.htmlFor = optInput.id;
            optLabel.textContent = option;

            optDiv.appendChild(optInput);
            optDiv.appendChild(optLabel);
            qDiv.appendChild(optDiv);
        });

        form.appendChild(qDiv);
    });

    // Submit button
    const submitBtn = document.createElement('button');
    submitBtn.type = 'submit';
    submitBtn.className = 'btn btn-primary mt-3';
    submitBtn.textContent = 'Submit Quiz';
    form.appendChild(submitBtn);

    // Results display
    const resultDiv = document.createElement('div');
    resultDiv.id = 'quiz-result';
    resultDiv.className = 'mt-4 fw-bold';
    form.appendChild(resultDiv);

    // Handle quiz submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        let correct = 0;
        let total = quizQuestions.length;
        let feedback = [];

        quizQuestions.forEach((q, idx) => {
            const selected = form.querySelector(`input[name="q${idx}"]:checked`);
            const userAnswer = selected ? selected.value : null;
            if (userAnswer === q.answer) {
                correct++;
                feedback.push(`<div class="text-success">Q${idx + 1}: Correct!</div>`);
            } else {
                feedback.push(`<div class="text-danger">Q${idx + 1}: Wrong. Correct answer: <b>${q.answer}</b></div>`);
            }
        });

        resultDiv.innerHTML = `<div class="mb-2">You scored <b>${correct}</b> out of <b>${total}</b>.</div>` + feedback.join('');
        window.scrollTo({ top: quizSection.offsetTop, behavior: 'smooth' });
    });

    quizSection.appendChild(form);

    // Hide other sections
    showResults(false);
    showUserSelect(false);
}
