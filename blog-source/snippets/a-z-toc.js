document.addEventListener('DOMContentLoaded', () => {
    fetch('/blog/articles.json')
        .then(response => response.json())
        .then(data => {
            const tocList = document.getElementById('tocList');

            const filteredArticles = data.articles.filter(article =>
                article.tags.includes('Dynamics365 A-Z') && 
                !article.link.includes("index.html")
            );

            // Group articles by letter
            const grouped = {};

            filteredArticles.forEach(article => {
                const match = article.link.match(/\/a-z\/([a-z])\//i);
                if (match) {
                    const letter = match[1].toUpperCase();
                    if (!grouped[letter]) {
                        grouped[letter] = [];
                    }
                    grouped[letter].push(article);
                }
            });

            // Sort letters alphabetically
            const letters = Object.keys(grouped).sort();

            letters.forEach(letter => {
                // Create Letter Heading
                const letterHeader = document.createElement('h3');
                letterHeader.textContent = letter;
                tocList.appendChild(letterHeader);

                // Create list for each letter
                const ul = document.createElement('ul');

                // Sort articles within each letter alphabetically
                grouped[letter].sort((a, b) => a.headline.localeCompare(b.headline));

                grouped[letter].forEach(article => {
                    const li = document.createElement('li');
                    const a = document.createElement('a');
                    a.href = article.link;
                    a.textContent = article.headline.split(' - ')[0]; // Use the first part of the headline
                    li.appendChild(a);
                    ul.appendChild(li);
                });

                tocList.appendChild(ul);
            });
        })
        .catch(err => console.error('Error fetching ToC data:', err));
});
