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

    // Function to switch views
    function showView(viewToShow) {
        Object.values(views).forEach(view => view.classList.add('hidden'));
        viewToShow.classList.remove('hidden');
    }

    // Event Listeners
    getStartedBtn.addEventListener('click', () => showView(views.questionInput));

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

    newQuestionBtn.addEventListener('click', () => {
        userQuestionInput.value = '';
        showView(views.questionInput);
    });

    // API interaction functions
    async function getRefinedQuestion(question) {
        const response = await fetch('/transform-question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question }),
        });
        if (!response.ok) {
            throw new Error('Failed to get refined question');
        }
        return response.json();
    }

    async function conductSurvey() {
        const response = await fetch('/approve-question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ approved: true }),
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
        // Removed the part that displays choices
    }

    function displayResults(data) {
        const resultsContent = document.getElementById('results-content');
        resultsContent.innerHTML = ''; // Clear previous results
    
        // Display key finding
        const keyFinding = document.createElement('div');
        keyFinding.innerHTML = `<h3>Key Finding</h3><p>${data.analysis.key_finding.replace(/^\d+\.\s*Key Finding:\s*/, '')}</p>`;
        resultsContent.appendChild(keyFinding);
    
        // Display quick stats
        const quickStats = document.createElement('div');
        quickStats.innerHTML = `<h3>Quick Stats</h3><ul>${data.analysis.quick_stats.map(stat => `<li>${stat.replace(/^\d+\.\s*Quick Stats:\s*-?\s*/, '')}</li>`).join('')}</ul>`;
        resultsContent.appendChild(quickStats);
    
        // Extract Fun Fact from Deep Thoughts and display Deep Thoughts
        let deepThoughtsText = data.analysis.interpretation;
        let funFactText = '';
        const funFactMatch = deepThoughtsText.match(/(\d+\.\s*Fun Fact:.*$)/s);
        if (funFactMatch) {
            funFactText = funFactMatch[1];
            deepThoughtsText = deepThoughtsText.replace(funFactMatch[0], '').trim();
        }
    
        const deepThoughts = document.createElement('div');
        deepThoughts.innerHTML = `<h3>Deep Thoughts</h3><p>${deepThoughtsText.replace(/^\d+\.\s*Interpretation:\s*/, '')}</p>`;
        resultsContent.appendChild(deepThoughts);
    
        // Display Fun Fact if available
        if (funFactText) {
            const funFact = document.createElement('div');
            funFact.innerHTML = `<h3>Fun Fact</h3><p>${funFactText.replace(/^\d+\.\s*Fun Fact:\s*/, '')}</p>`;
            resultsContent.appendChild(funFact);
        }
    }
});