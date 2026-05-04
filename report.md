LLM YouTube Channel Monitor - Project Report
1. Problem Statement
goal:
Build a concise table that categorises videos: who is speaking, which topics they cover, and how the channels relate to each other on LLM themes.
Host the table and supporting material on a public page so reviewers can open it in a browser. The solution should keep running so the table stays updated as new videos appear.
Use AI to transcribe the videos (or reliable captions) and fold that into the table so each row reflects what that popular creator actually says about LLM topics—not only the title or thumbnail.
2.Methodology
(i)API: YouTube API: Fetch video list (title, date, video ID)
        YouTube Transcript API: Get English transcripts
        Zhipu AI (GLM-4-Flash): Extract topics, generate summary, analyze relations
(ii)SQLite Database: Store video info and analysis
(iii)HTML Table Generation: Display Channel, Title, Topics, Relation, Summary
(iv)channels:  "Andrej Karpathy": "UCXUPKJO5MZQN11PqgIvyuvQ",
    "Matthew Berman": "UCawZsQWqfGSbCI5yjkdVkTA",
    "Matt Wolfe": "UChpleBmo18P08aKCIgti38g"
(v)Automation Flow: GitHub Actions + Pages

The system runs automatically every 6 hours via GitHub Actions:
1. Call YouTube API to fetch latest videos from each channel
2. Check database to skip already processed videos
3. Fetch video transcripts (if available)
4. Call Zhipu AI to analyze content
5. Store results in database
6. Update HTML table
7. Push to GitHub Pages for public access

3.Experimental Results
The system tracks 3 channels, fetching the latest 5 videos from each, analyzing the topics, relations, and summaries.
screenshot:
<img width="2837" height="1631" alt="image" src="https://github.com/user-attachments/assets/f7fa2165-c9f8-4d47-907a-05a2f93b76d8" />
<img width="2783" height="1556" alt="image" src="https://github.com/user-attachments/assets/b414f431-3c5c-4030-b1d3-3fceb5e24c47" />
<img width="2821" height="1126" alt="image" src="https://github.com/user-attachments/assets/c97ff93a-fa4d-42f7-870b-b9525847541f" />

github link: https://github.com/irisiyuj/llm_youtube

# References
- YouTube Data API v3: https://developers.google.com/youtube/v3
- youtube-transcript-api: https://github.com/jdepoix/youtube-transcript-api
- Zhipu AI Open Platform: https://open.bigmodel.cn/
- GitHub Actions: https://docs.github.com/en/actions
- GitHub Pages: https://pages.github.com/

Note: This project was completed with the assistance of AI(deepseek).
Due to the time limit, it's not polished/ optimized/ may contain error.
