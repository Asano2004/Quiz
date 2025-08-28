-- データベース初期化スクリプト
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- usersテーブル
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- quizzesテーブル
CREATE TABLE IF NOT EXISTS quizzes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    question TEXT NOT NULL,
    choices JSON NOT NULL,
    answer INT NOT NULL,
    category VARCHAR(50) NOT NULL,
    difficulty VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- answersテーブル
CREATE TABLE IF NOT EXISTS answers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    quiz_id INT NOT NULL,
    selected INT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 管理者ユーザーを作成
INSERT INTO users (username, password, is_admin) VALUES 
('admin', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', TRUE);
-- パスワードは 'secret123' (SHA256でハッシュ化)

-- サンプルクイズデータ
INSERT INTO quizzes (user_id, question, choices, answer, category, difficulty) VALUES
(1, '日本の首都はどこですか？', '["東京", "大阪", "名古屋", "福岡"]', 0, '地理', 'easy'),
(1, 'Pythonで使用される主要なWebフレームワークは？', '["Flask", "Django", "FastAPI", "すべて正しい"]', 3, 'プログラミング', 'medium'),
(1, '1 + 1 = ?', '["1", "2", "3", "4"]', 1, '数学', 'easy'),
(1, '世界で最も高い山は？', '["富士山", "エベレスト", "キリマンジャロ", "マッキンリー"]', 1, '地理', 'medium'),
(1, 'HTMLの正式名称は？', '["HyperText Markup Language", "High Tech Modern Language", "Home Tool Markup Language", "Human Text Management Language"]', 0, 'プログラミング', 'medium'),
(1, 'オリンピックは何年に一度開催されますか？', '["2年", "3年", "4年", "5年"]', 2, 'スポーツ', 'easy'),
(1, 'サッカーのワールドカップで最多優勝国は？', '["ドイツ", "アルゼンチン", "ブラジル", "イタリア"]', 2, 'スポーツ', 'medium'),
(1, '光の速度は秒速約何キロメートル？', '["30万km", "150万km", "300万km", "3000万km"]', 0, '科学', 'medium'),
(1, 'プログラミング言語Javaを開発した会社は？', '["Microsoft", "Google", "Sun Microsystems", "Apple"]', 2, 'プログラミング', 'hard'),
(1, '日本の47都道府県で面積が最も大きいのは？', '["北海道", "岩手県", "福島県", "長野県"]', 0, '地理', 'medium');