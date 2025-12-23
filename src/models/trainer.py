import pandas as pd
import joblib
import os
import logging
import numpy as np
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def train_layout_model():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL is missing.")
        return

    engine = create_engine(db_url)
    
    # 1. Load Data including new dimensions (width, height)
    logger.info("Loading data from database...")
    query = "SELECT pdf_id, page_number, font_size, is_bold, x0, y0, width, height, label FROM layout_features"
    try:
        df = pd.read_sql(query, engine)
    except Exception as e:
        logger.error(f"Database error: {e}")
        return
    
    if df.empty:
        logger.error("No data found. Please run seed_data.py and then pdf_processor.py.")
        return

    # 2. Preprocessing
    df['is_bold'] = df['is_bold'].fillna(False).astype(int)
    df['font_size'] = df['font_size'].fillna(0)
    df['label'] = df['label'].fillna('body')
    
    # Sort for context calculation
    df = df.sort_values(['pdf_id', 'page_number', 'y0']).reset_index(drop=True)

    # 3. Feature Engineering
    # Distance from previous line (context)
    df['dist_prev_y'] = df.groupby(['pdf_id', 'page_number'])['y0'].diff().fillna(0)
    
    # Center deviation (assuming standard ~600pt width for features)
    df['center_dev'] = abs(300 - (df['x0'] + df['width']/2))
    
    df['is_first_page'] = (df['page_number'] == 0).astype(int)
    
    # Relative font size (Z-score per PDF)
    df['rel_font_size'] = df.groupby('pdf_id')['font_size'].transform(
        lambda x: (x - x.mean()) / (x.std() + 0.001) if x.std() > 0 else 0
    )

    # NEW: Shape features
    # Aspect ratio (avoid div by zero)
    df['aspect_ratio'] = df['width'] / (df['height'] + 0.1) 

    features = [
        'font_size', 'rel_font_size', 'is_bold', 
        'x0', 'y0', 'width', 'dist_prev_y', 
        'center_dev', 'is_first_page', 'aspect_ratio'
    ]
    
    # Clean data for training
    df = df.dropna(subset=features + ['label'])
    
    X = df[features]
    y = df['label']

    logger.info(f"Training with {len(X)} samples. Features: {features}")

    # 4. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 5. Model Initialization
    model = RandomForestClassifier(
        n_estimators=200, 
        max_depth=15,
        min_samples_leaf=4,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1 # Use all cores
    )
    
    model.fit(X_train, y_train)

    # 6. Evaluation
    y_pred = model.predict(X_test)
    logger.info("\n--- Model Performance ---")
    logger.info(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred))

    # 7. Export
    output_dir = 'src/models/export'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'layout_model.joblib')
    joblib.dump(model, output_path)
    logger.info(f"Model saved to {output_path}")

if __name__ == "__main__":
    train_layout_model()