# 🚀 Simple Steps to Deploy NailVital AI to Render

Follow these exact steps to get your backend live.

## 1. Push Your Code to GitHub
Render needs your code to be on GitHub or GitLab.
- Create a new repository on GitHub (e.g., `nailvital-backend`).
- Run these commands in your `NailVital_AI_Backend` folder:
  ```bash
  git init
  git add .
  git commit -m "Prepare for Render"
  git branch -M main
  git remote add origin https://github.com/YOUR_USERNAME/nailvital-backend.git
  git push -u origin main
  ```

## 2. Connect to Render
- Go to [dashboard.render.com](https://dashboard.render.com).
- Click **New** > **Web Service**.
- Connect your GitHub account and select the `nailvital-backend` repository.

## 3. Configure the Service
Render will automatically detect your `render.yaml` or you can set these manually:
- **Language**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## 4. Set Up a Database (Mandatory)
You have two great free options:

### Option A: Render PostgreSQL (Easiest)
*(Free for 90 days, then expires)*
1.  **Go to Render Dashboard** > **New** > **PostgreSQL**.
2.  **Name it**: `nailvital-db`.
3.  Click **Create Database**.
4.  Copy the **Internal Database URL**.
5.  Add it to your Web Service **Environment** as `DATABASE_URL`.

### Option B: Supabase (Recommended - Permanent Free Tier)
*(Better for long-term use)*
1.  Go to [supabase.com](https://supabase.com) and create a free account.
2.  Create a **New Project** named `NailVital`.
3.  Set a **Database Password** (Save it!).
4.  Once the project is ready, go to **Project Settings** > **Database**.
5.  Look for **Connection string** > **URI**.
6.  It will look like: `postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres`
7.  **Replace `[YOUR-PASSWORD]`** with the password you created.
8.  Add this full URI to your Render Web Service **Environment** as `DATABASE_URL`.

## 5. Set Environment Variables
In the Render dashboard, go to the **Environment** tab and add:
- `GROQ_API_KEY`: Your Groq API Key (Mandatory for Chat).
- `GEMINI_API_KEY`: (Optional) Only add this if you want to use Google Gemini features.
- `DATABASE_URL`: (The URL from step 4).

## 6. Verify the Deployment
- Once the build is finished, Render will provide a URL (e.g., `https://nailvital-backend.onrender.com`).
- Visit that URL in your browser. You should see:
  `{"message": "Welcome to NailVital AI API"}`

---
### 🛠️ Troubleshooting

#### 1. Machine Learning Error (`tflite-runtime`)
If you see an error like `No module named 'tflite_runtime'`, Render's environment might be missing some system libraries.
- Try changing your `requirements.txt` from `tflite-runtime` to `tensorflow-cpu` (this is larger but more compatible). Or simply ensure you are using **Python 3.10** as specified in `render.yaml`.

#### 2. Database Connection Error
If the app fails to start, check your `DATABASE_URL`.
- Ensure it starts with `postgresql://` (Supabase URLs are usually correct, but `main.py` handles the `postgres://` vs `postgresql://` fix automatically).
- Make sure you've allowed connections from anywhere (0.0.0.0/0) in your Supabase dashboard settings.

#### 3. Uploads Folder
Render has an ephemeral filesystem. This means images uploaded to `/uploads` will disappear when the app restarts.
- For a production app, you would eventually want to use **Supabase Storage** or **Cloudinary**, but for now, the local `/uploads` will work for testing!
