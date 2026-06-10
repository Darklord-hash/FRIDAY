from ddgs import DDGS
import requests
import webbrowser


def search_web(query, max_results=3):
    """Search the web using DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results, region='wt-wt')
            if not results:
                return "No results found, Boss."

            summary = f"Here's what I found, Boss:\n"
            for i, result in enumerate(results, 1):
                if isinstance(result, dict):
                    title = result.get('title', 'No title')
                    body = result.get('body', result.get('snippet', 'No description'))
                    href = result.get('href', result.get('link', ''))
                else:
                    title = getattr(result, 'title', 'No title')
                    body = getattr(result, 'body', getattr(result, 'snippet', 'No description'))
                    href = getattr(result, 'href', getattr(result, 'link', ''))

                summary += f"\n{i}. {title}: {body[:150]}..."
                if href:
                    summary += f" ({href})"

            return summary
    except Exception as e:
        return f"Search error, Boss: {str(e)}"


def search_youtube(query):
    """Search YouTube and open results in browser."""
    try:
        # Build YouTube search URL
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

        # Open browser
        webbrowser.open(search_url)

        # Also get some results via DuckDuckGo for speaking
        with DDGS() as ddgs:
            yt_query = f"site:youtube.com {query}"
            results = ddgs.text(yt_query, max_results=2, region='wt-wt')

            if results:
                summary = f"Opening YouTube search for '{query}', Boss. Top results:\n"
                for i, result in enumerate(results, 1):
                    if isinstance(result, dict):
                        title = result.get('title', 'No title')
                    else:
                        title = getattr(result, 'title', 'No title')
                    summary += f"\n{i}. {title[:100]}"
                return summary
            else:
                return f"Opening YouTube search for '{query}', Boss."

    except Exception as e:
        # Fallback: just open YouTube
        webbrowser.open(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")
        return f"Opening YouTube search for '{query}', Boss."


def search_news(query, max_results=3):
    """Search news using DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = ddgs.news(query, max_results=max_results, region='wt-wt')
            if not results:
                return "No news found, Boss."

            summary = f"Latest news, Boss:\n"
            for i, result in enumerate(results, 1):
                if isinstance(result, dict):
                    title = result.get('title', 'No title')
                    body = result.get('body', result.get('snippet', 'No description'))
                    source = result.get('source', 'Unknown')
                    date = result.get('date', '')
                else:
                    title = getattr(result, 'title', 'No title')
                    body = getattr(result, 'body', getattr(result, 'snippet', 'No description'))
                    source = getattr(result, 'source', 'Unknown')
                    date = getattr(result, 'date', '')

                summary += f"\n{i}. {title} ({source}, {date}): {body[:150]}..."

            return summary
    except Exception as e:
        return f"News search error, Boss: {str(e)}"


def get_wikipedia_summary(query):
    """Get Wikipedia summary."""
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            title = data.get('title', query)
            extract = data.get('extract', 'No summary available.')
            return f"Wikipedia says about {title}, Boss: {extract[:400]}..."
        else:
            return f"Couldn't find Wikipedia article for {query}, Boss."
    except Exception as e:
        return f"Wikipedia error, Boss: {str(e)}"


def get_instant_answer(query):
    """Get instant answer from DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = ddgs.answers(query)
            if results:
                if isinstance(results[0], dict):
                    answer = results[0].get('text', results[0].get('answer', ''))
                else:
                    answer = getattr(results[0], 'text', getattr(results[0], 'answer', ''))

                if answer:
                    return f"Quick answer, Boss: {answer}"

            return search_web(query, max_results=2)
    except Exception as e:
        return search_web(query, max_results=2)