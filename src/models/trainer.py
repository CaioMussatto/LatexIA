import pandas as pd
import joblib
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

def train_layout_model():
    load_dotenv()
    engine = create_engine(os.getenv("DATABASE_URL"))
    
    query = "SELECT pdf_id, page_number, font_size, is_bold, x0, y0, label FROM layout_features"
    df = pd.read_sql(query, engine)
    
    if df.empty:
        print("Error: No data found in layout_features. Execute the processor first.")
        return

    df['is_bold'] = df['is_bold'].fillna(False).astype(int)
    df['font_size'] = df['font_size'].fillna(0)
    df['label'] = df['label'].fillna('unknown')

    df = df.sort_values(['pdf_id', 'page_number', 'y0']).reset_index(drop=True)

    df['dist_prev_y'] = df.groupby(['pdf_id', 'page_number'])['y0'].diff().fillna(0)
    df['center_dev'] = abs(300 - df['x0'])
    df['is_first_page'] = (df['page_number'] == 0).astype(int)
    
    df['rel_font_size'] = df.groupby('pdf_id')['font_size'].transform(
        lambda x: (x - x.mean()) / (x.std() + 0.001) if x.std() > 0 else 0
    )

    features = ['font_size', 'rel_font_size', 'is_bold', 'x0', 'y0', 'dist_prev_y', 'center_dev', 'is_first_page']
    X = df[features]
    y = df['label']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(
        n_estimators=200, 
        max_depth=12,
        min_samples_leaf=5,
        class_weight='balanced',
        random_state=42
    )
    
    print(f"Training model: {len(X_train)} samples identified for training")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\nModel Performance Audit")
    print(f"Accuracy Score: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred))

    os.makedirs('src/models/export', exist_ok=True)
    joblib.dump(model, 'src/models/export/layout_model.joblib')
    print("Model training completed and exported to src/models/export/layout_model.joblib")

if __name__ == "__main__":
    train_layout_model()