# API Setup — AI-FactShield Pro

## 1. NewsAPI
Create a NewsAPI key and set:

```env
NEWS_API_KEY=your_key_here
```

The backend uses the `X-Api-Key` header rather than exposing the key in browser URLs.

## 2. GNews
Create a GNews key and set:

```env
GNEWS_API_KEY=your_key_here
```

GNews is used for current/search news and language/country filtering.

## 3. Google Fact Check Tools
If available for the deployment:

```env
GOOGLE_FACTCHECK_API_KEY=your_key_here
```

This adds fact-check evidence to verification. It does not automatically make every claim false or true.

## 4. Render
Add the variables in the Render service's Environment settings. Do not put secrets in `templates/`, JavaScript, Git, or the ZIP.

## 5. Health endpoint
After deployment, open:

`/live-news/api/health`

It reports which providers are configured without exposing secret values.
