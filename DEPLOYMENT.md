# Deployment Guide for Meal Nutrition Analyzer

This guide provides specific instructions for deploying the Meal Nutrition Analyzer on Hugging Face Spaces.

## Configuration Files

1. **Main Configuration**: `.huggingface.yaml` (with dot prefix)
   - Uses Streamlit SDK
   - Points to `app.py` as the main application file
   - Sets Python version to 3.10

2. **Dependencies**: `requirements.txt`
   - streamlit>=1.22.0
   - pillow>=9.0.0
   - groq>=0.4.0
   - requests>=2.28.0
   - python-dotenv>=0.19.0

## Troubleshooting Deployment Issues

If deployment fails, check the following:

1. Make sure no conflicting configuration files exist 
   - Removed/renamed any alternate huggingface.yaml files
   - Only ONE .huggingface.yaml file should exist (with the dot prefix)

2. Check that app.py contains valid Streamlit code
   - Added error logging to help identify issues
   - Fixed potential variable scope issues

3. Verify that requirements.txt contains all necessary dependencies
   - All dependencies are correctly specified
   - No conflicting dependencies

4. Review Hugging Face Spaces logs for specific error messages
   - May need to enable more verbose logging

## Local Testing

Before deploying, test locally using:

```bash
streamlit run app.py
```

## Deployment Process

1. Commit all changes to your repository
2. Push changes to the branch connected to Hugging Face Spaces
3. Monitor deployment logs on Hugging Face for any issues

## User Instructions

Users will need to:
1. Enter their Groq API key
2. Upload a meal image
3. Select their nutrition focus and health goals
4. Click "Analyze Meal" to get results
