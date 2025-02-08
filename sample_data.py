import pandas as pd

# Create sample data
data = {
    'textid': ['T001', 'T002', 'T003'],
    'source': [
        'Hello, how are you?',
        'The weather is nice today.',
        'I love programming!'
    ],
    'extra': [
        'Casual greeting',
        'Weather comment',
        'Enthusiastic statement'
    ],
    'CHT': [
        '你好,你好嗎?',
        '今天天氣很好。',
        '我喜歡寫程式!'
    ],
    'JA': [
        'こんにちは、お元気ですか?',
        '今日は良い天気ですね。',
        'プログラミングが大好きです!'
    ],
    'KO': [
        '안녕하세요, 어떠세요?',
        '오늘 날씨가 좋네요.',
        '저는 프로그래밍을 좋아해요!'
    ]
}

# Create DataFrame
df = pd.DataFrame(data)

# Save to Excel
df.to_excel('sample_texts.xlsx', index=False)
print("Sample Excel file 'sample_texts.xlsx' created successfully.")