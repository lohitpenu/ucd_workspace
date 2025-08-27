import os
import io
import base64
import json
import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for Django
import matplotlib.pyplot as plt

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages, auth
from django.contrib.auth import logout


from drive_app.views import upload_user_file, list_drive_files, download_file, delete_file
from drive_app.utils import upload_to_google_drive, ensure_drive_authenticated, process_image_and_upload



# Create your views here.
def home(request):
    return render(request, 'home.html')

@csrf_exempt
def process_image_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed.'}, status=405)

    auth_check = ensure_drive_authenticated(request, api_mode=True)
    if auth_check:
        return auth_check

    image_url = request.POST.get('image_url')
    if not image_url:
        return JsonResponse({'error': 'Missing image_url parameter.'}, status=400)

    try:
        result = process_image_and_upload(request.session['credentials'], image_url)
        return JsonResponse(result)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'RequestException: {e}'}, status=502)
    except IOError as e:
        return JsonResponse({'error': f'IOError: {e}'}, status=500)

def logout_view(request):
    # Revoke Google OAuth token if present
    creds = request.session.get('credentials')
    if creds and 'token' in creds:
        try:
            requests.post(
                'https://oauth2.googleapis.com/revoke',
                params={'token': creds['token']},
                headers={'content-type': 'application/x-www-form-urlencoded'},
                timeout=5
            )
        except requests.RequestException:
            pass  # Don’t block logout if revoke fails

    # Clear everything
    request.session.flush()   # Clears *all* session data and deletes the session cookie
    logout(request)           # Logs out Django user (extra safety)

    return render(request, "logged_out.html")

def login_view(request):
    """
    Redirects to Google Drive authentication.
    """
    if 'credentials' in request.session:
        # If already authenticated, redirect to home or another page
        return redirect('home')
    # Redirect to Google Drive authentication
    return redirect('google_drive_auth')  # Assuming 'google_drive_auth' is defined in drive_app.urls


# View that receives or prepares the CSV
def input_csv_view(request):
    csv_path = os.path.join(settings.MEDIA_ROOT, "processed/last_csv/cluster_growth.csv")

    if not os.path.exists(csv_path):
        messages.error(request, "CSV file not found. Please upload or generate it first.")
        return redirect("plot_clusters")  # or wherever you want to go when missing

    try:
        with open(csv_path, "r") as f:
            csv_content = f.read()
        request.session["csv_data"] = csv_content
        messages.success(request, "CSV file loaded successfully!")
    except Exception as e:
        messages.error(request, f"Error loading CSV file: {e}")

    return redirect("plot_clusters")

# View that generates plots
def plot_clusters_view(request):
    csv_content = request.session.get("csv_data")
    if not csv_content:
        #messages.error(request, "No CSV data found. Please upload or reload a CSV file.")
        return redirect("home")  # send back to upload/reload page

    # Load into DataFrame
    df = pd.read_csv(io.StringIO(csv_content))

    # Swap Image # and Cluster Tracking ID
    df[["Image #", "Cluster Tracking ID"]] = df[["Cluster Tracking ID", "Image #"]]

    plot_images = []

    # Create a single figure with 3 rows (1 column layout)
    fig, axes = plt.subplots(1, 2, figsize=(18, 6), constrained_layout=True)

    # Plot 1: Cluster Pixel Area per Cluster Tracking ID
    ax = axes[0]
    for img_id in df["Image #"].unique():
        subset = df[df["Image #"] == img_id]
        ax.plot(subset["Cluster Tracking ID"], (subset["Cluster Pixel Area"]/100), 
                marker='o', label=f'Cluster {img_id}')
    ax.set_title("Cluster Pixel Area per Cluster Tracking ID")
    ax.set_xlabel("Image at different Time Steps")
    ax.set_ylabel("Cluster Pixel Area (in cm2)")
    ax.legend(title="Cluster Number")
    ax.grid(True)

    # Plot 2: Relative Cluster Area vs Cluster Pixel Area
    # ax = axes[1]
    # scatter = ax.scatter((df["Cluster Pixel Area"]/100), df["Relative Cluster Area"], 
    #                      c=df["Cluster Tracking ID"], cmap='coolwarm', alpha=0.7, vmin=0, vmax=4)
    # cbar = plt.colorbar(scatter, ax=ax, orientation='vertical')
    # cbar.set_label("Cluster ID")
    # ax.set_title("Relative Cluster Area vs Cluster Pixel Area")
    # ax.set_xlabel("Cluster Pixel Area (in cm2)")
    # ax.set_ylabel("Relative Cluster Area")
    # ax.grid(True)

    # Plot 3: Cluster Height vs Width
    ax = axes[1]
    scatter = ax.scatter(df["Cluster Width"], df["Cluster Height"], 
                         c=df["Image #"], cmap='tab10', alpha=0.7)
    ax.set_title("Cluster Height vs Cluster Width")
    ax.set_xlabel("Cluster Width")
    ax.set_ylabel("Cluster Height")
    ax.grid(True)
    ax.legend(*scatter.legend_elements(), title="Cluster")

    plot_images.append(fig_to_base64(fig))

    return render(request, "home.html", {"plots": plot_images})

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return img_base64