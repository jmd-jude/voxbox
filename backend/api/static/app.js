document.addEventListener('DOMContentLoaded', () => {
    // Get all view elements
    const views = {
        landing: document.getElementById('landing'),
        questionInput: document.getElementById('question-input'),
        questionRefinement: document.getElementById('question-refinement'),
        loading: document.getElementById('loading'),
        results: document.getElementById('results')
    };

    // Get interactive elements
    const getStartedBtn = document.getElementById('get-started');
    const userQuestionInput = document.getElementById('user-question');
    const generatePollBtn = document.getElementById('generate-poll');
    const approveQuestionBtn = document.getElementById('approve-question');
    const tryAgainBtn = document.getElementById('try-again');
    const newQuestionBtn = document.getElementById('new-question');
    const revealButton = document.getElementById('reveal-button');
    const additionalResults = document.getElementById('additional-results');

    // Function to switch views
    function showView(viewToShow) {
        Object.values(views).forEach(view => view.classList.add('hidden'));
        viewToShow.classList.remove('hidden');
    }

    // Session management function
    function getOrCreateSessionId() {
        let sessionId = localStorage.getItem('sessionId');
        if (!sessionId) {
            sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('sessionId', sessionId);
        }
        return sessionId;
    }

    // New: Start new survey session
    async function startNewSurvey() {
        try {
            const response = await fetch('/start-new-survey', {
                method: 'POST'
            });
            const data = await response.json();
            if (data.session_id) {
                console.log('New survey started with session ID:', data.session_id);
                localStorage.setItem('sessionId', data.session_id);
            } else {
                console.error('Failed to start new survey:', data.error);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    // Event Listeners
    getStartedBtn.addEventListener('click', async () => {
        await startNewSurvey();
        showView(views.questionInput);
    });

    generatePollBtn.addEventListener('click', async () => {
        const userQuestion = userQuestionInput.value.trim();
        if (userQuestion) {
            showView(views.loading);
            try {
                const refinedQuestionData = await getRefinedQuestion(userQuestion);
                displayRefinedQuestion(refinedQuestionData);
                showView(views.questionRefinement);
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
                showView(views.questionInput);
            }
        } else {
            alert('Please enter a question.');
        }
    });

    approveQuestionBtn.addEventListener('click', async () => {
        showView(views.loading);
        try {
            const results = await conductSurvey();
            displayResults(results);
            showView(views.results);
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
            showView(views.questionInput);
        }
    });

    tryAgainBtn.addEventListener('click', () => showView(views.questionInput));

    newQuestionBtn.addEventListener('click', async () => {
        userQuestionInput.value = '';
        await startNewSurvey();
        showView(views.questionInput);
    });

    // New: Reveal button event listener
    revealButton.addEventListener('click', () => {
        additionalResults.classList.remove('hidden');
        newQuestionBtn.classList.remove('hidden');
        revealButton.classList.add('hidden');
    });

    // API interaction functions
    async function getRefinedQuestion(question) {
        const sessionId = getOrCreateSessionId();
        const response = await fetch('/transform-question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question, session_id: sessionId }),
        });
        if (!response.ok) {
            throw new Error('Failed to get refined question');
        }
        return response.json();
    }

    async function conductSurvey() {
        const sessionId = getOrCreateSessionId();
        const response = await fetch('/approve-question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ approved: true, session_id: sessionId }),
        });
        if (!response.ok) {
            throw new Error('Failed to conduct survey');
        }
        return response.json();
    }

    // Display functions
    function displayRefinedQuestion(data) {
        document.getElementById('original-question').textContent = `Your question: ${data.original_question}`;
        document.getElementById('refined-question').textContent = `Refined question: ${data.transformed_question.question}`;
    }

    function displayResults(data) {
        // Display key finding
        document.getElementById('key-finding-text').textContent = data.analysis.key_finding;

        // Prepare quick stats
        const quickStatsList = document.getElementById('quick-stats-list');
        quickStatsList.innerHTML = '';
        data.analysis.quick_stats.forEach(stat => {
            const li = document.createElement('li');
            li.textContent = stat;
            quickStatsList.appendChild(li);
        });

        // Display in their voices (formerly deep thoughts)
        const inTheirVoicesContainer = document.getElementById('in-their-voices-text');
        inTheirVoicesContainer.innerHTML = ''; // Clear previous content
        if (Array.isArray(data.analysis.interpretation)) {
            data.analysis.interpretation.forEach(person => {
                const personDiv = document.createElement('div');
                personDiv.innerHTML = `
                    <p><strong>${person.name}, ${person.age}</strong> - ${person.description}</p>
                    <p><em>"${person.quote}"</em></p>
                `;
                inTheirVoicesContainer.appendChild(personDiv);
            });
        } else {
            inTheirVoicesContainer.textContent = "No interpretation data available.";
        }

        // Display fun fact
        document.getElementById('fun-fact-text').textContent = data.analysis.fun_fact;

        // Show reveal button, hide additional results and "Let's Go Again" button
        revealButton.classList.remove('hidden');
        additionalResults.classList.add('hidden');
        newQuestionBtn.classList.add('hidden');

        // Trigger confetti
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });
    }
});