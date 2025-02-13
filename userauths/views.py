from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
import random
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm


from userauths.models import User
from userauths.forms import UserRegisterForm


def generate_otp():
    return str(random.randint(100000, 999999))

def RegisterView(request):
    if request.user.is_authenticated:
        messages.warning(request, "Bạn đã đăng nhập rồi.")
        return redirect("account:account")
    
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            
            new_user = form.save(commit=False)
            new_user.is_active = False
            
            
            new_user.otp = generate_otp()
            new_user.otp_expiry = timezone.now() + timezone.timedelta(minutes=5)
            new_user.save()
            
            
            send_mail(
                "Verify your account.",
                f"Your OTP: {new_user.otp}",
                "th.tran0522@gmail.com", 
                [new_user.email],
                fail_silently=False,
            )
            
            
            request.session['user_id'] = new_user.id
            return redirect("userauths:verify-otp")
    else:
        form = UserRegisterForm()
    
    context = {"form": form}
    return render(request, "userauths/sign-up.html", context)

def VerifyOTPView(request):
    user_id = request.session.get('user_id')
    
   
    if not user_id:
        messages.error(request, "Please, register again!")
        return redirect("userauths:sign-up")
    
    user = User.objects.get(id=user_id)
    
    
    if request.method == "POST":
        otp_entered = request.POST.get("otp")
        
        if user.otp == otp_entered and timezone.now() < user.otp_expiry:
            
            user.is_active = True
            user.save()
            login(request, user)
            del request.session['user_id'] 
            messages.success(request, "Verify successfull!")
            return redirect("account:account")
        else:
            messages.error(request, "Invalid OTP!")
            return redirect("userauths:verify-otp")
    
    return render(request, "userauths/verify_otp.html")

def ResendOTPView(request):
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.error(request, "Please, register again!")
        return redirect("userauths:sign-up")
    
    user = User.objects.get(id=user_id)
    
    
    user.otp = generate_otp()
    user.otp_expiry = timezone.now() + timezone.timedelta(minutes=5)
    user.save()
    
    send_mail(
                "Verify your account.",
                f"Your otpotp: {user.otp}",
                "th.tran0522@gmail.com", 
                [user.email],
                fail_silently=False,
            )
    
    messages.success(request, "OTP resent. Please check email.")
    return redirect("userauths:verify-otp")

def LoginView(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, email=email, password=password)

            if user is not None: 
                login(request, user)
                messages.success(request, "You are logged.")
                return redirect("account:account")
            else:
                messages.warning(request, "Username or password does not exist")
                return redirect("userauths:sign-in")
        except:
            messages.warning(request, "User does not exist")

    if request.user.is_authenticated:
        messages.warning(request, "You are already logged In")
        return redirect("account:account")
        
    return render(request, "userauths/sign-in.html")

def logoutView(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("userauths:sign-in")
