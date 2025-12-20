# How to Deploy Your Website

Since you want to share your website with friends, the easiest way is to use **Netlify Drop**. It is free and doesn't require complex setup.

## Step 1: Build Your Project
First, we need to create a production-ready version of your app.

1.  Open your terminal in the `frontend` folder.
2.  Run the build command:
    ```bash
    npm run build
    ```
3.  This will create a new folder called `dist` in your project directory. This folder contains your optimized website.

## Step 2: Deploy to Netlify
1.  Go to [Netlify Drop](https://app.netlify.com/drop).
2.  You might need to sign up for a free account.
3.  Once logged in, you will see a "Drag and drop your site output folder here" area.
4.  Open your file explorer on your computer and find the `dist` folder inside `frontend`.
5.  Drag the **entire `dist` folder** and drop it onto the Netlify page.

## Step 3: Share the Link
1.  Netlify will upload your files and give you a random URL (e.g., `peaceful-galaxy-123456.netlify.app`).
2.  You can copy this link and send it to your friends!
3.  (Optional) You can change the site name in "Site Settings" to something more readable.

## Alternative: Vercel
If you plan to put your code on GitHub, you can use Vercel:
1.  Push your code to a GitHub repository.
2.  Go to [Vercel.com](https://vercel.com) and sign up.
3.  Click "Add New Project" and select your GitHub repository.
4.  Click "Deploy". Vercel will handle the rest and update your site automatically whenever you push code.
