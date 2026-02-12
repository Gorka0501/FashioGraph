# User Guide - Accounts

User account management, authentication, and profile settings.

## Account Basics

### Creating an Account

1. **Launch Application**
   - Web: Navigate to `http://localhost:8501`
   - Desktop: Run `python start_desktop.py`
   - Mobile: Install and open app

2. **Register**
   - Enter unique username (3-50 characters)
   - Create strong password (8+ chars, uppercase, lowercase, digit)
   - Click "Create Account"

3. **Verification**
   - Account created immediately
   - No email confirmation needed
   - Can login right away

### Logging In

**Web/Desktop:**
1. Open application
2. Enter username
3. Enter password
4. Click "Login"
5. Redirected to dashboard

**Mobile:**
1. Open app
2. Tap "Sign In"
3. Enter credentials
4. Tap "Login"

### Staying Signed In

The application automatically maintains sessions:
- **Session Duration**: 24 hours
- **Auto-Logout**: After 24 hours of last activity
- **Multiple Devices**: Each device has separate session
- **Single User Per Device**: Logging in as new user logs out previous user

---

## Password Security

### Password Requirements

Your password must include:
- ✅ **At least 8 characters**
- ✅ **One uppercase letter** (A-Z)
- ✅ **One lowercase letter** (a-z)
- ✅ **One digit** (0-9)
- ✅ **Recommended: Special character** (!@#$%^&*)

### Password Examples

| Password | Valid | Reason |
|----------|-------|--------|
| `MyPass123!` | ✅ | Meets all requirements |
| `SecurePass456` | ✅ | Has all required types |
| `password` | ❌ | Too simple, no uppercase/digit |
| `Pass123` | ❌ | Only 7 characters |
| `ALLUPPERCASE1` | ❌ | No lowercase letter |

### Best Practices

1. **Don't share** your password with anyone
2. **Don't reuse** passwords from other accounts
3. **Change regularly** every 3-6 months
4. **Use memorable but unique** combinations
5. **Don't write down** or share via email

---

## Changing Password

### Steps

1. **Open Settings**
   - Click profile icon → Settings
   - Or navigate to Settings page

2. **Select "Change Password"**
   - Located in Account section

3. **Enter Current Password**
   - For verification

4. **Enter New Password** (twice)
   - Must meet security requirements
   - Must be different from current

5. **Save**
   - Click "Update Password"
   - You'll remain logged in

### After Changing

- ✅ New password takes effect immediately
- ✅ Old password no longer works
- ✅ Other sessions not affected

---

## Resetting Forgotten Password

### If You Forgot Your Password

**Current Limitation:** Password reset via email not yet implemented.

**Solutions:**
1. **Create New Account**
   - Use different username
   - Setup wardrobe and items fresh

2. **Contact Administrator**
   - Provide username and proof of ownership
   - Admin can reset for you (future feature)

**Future Enhancement:** Email-based password reset coming in next version.

---

## Profile Information

### Viewing Profile

1. Click profile icon (top right)
2. Select "My Profile"
3. View account details:
   - Username
   - Account creation date
   - Last login date
   - Item count
   - Outfit history

### Profile Details

```
Username:         john_doe
Member Since:     January 1, 2024
Last Login:       Today at 10:30 AM
Wardrobe Items:   25
Generated Outfits: 42
Rated Outfits:    10
```

---

## Device Management

### Current Device

**Web/Desktop Applications:**
- One active session per device type
- Each device stores its own session
- Sessions independent from other devices

**Mobile App:**
- One session per device
- Multiple devices can have different users

### Example Scenario

```
Device 1 (Laptop):     User A logged in
Device 2 (Phone):      User B logged in
Device 3 (Desktop):    User A logged in (different session)

Result: User A has 2 sessions, User B has 1 session
All can access their data independently
```

### Managing Sessions

1. **View Active Sessions**
   - Settings → Sessions
   - Shows devices and login times

2. **Logout from Device**
   - Click "Logout" button
   - Session ends immediately
   - Need to login again to use app

3. **Logout All Other Sessions**
   - Settings → Advanced
   - "Logout all other sessions"
   - Remains logged in on current device only

---

## Account Settings

### Available Settings

#### Privacy
- Make profile public/private (future feature)
- Control data sharing (future feature)

#### Notifications
- Email notifications (enable/disable)
- Notification frequency

#### Display
- Dark mode / Light mode
- Language (if multilingual)
- Units (metric/imperial for sizes)

#### Data
- Download personal data
- Delete account (with confirmation)

### Accessing Settings

1. Click profile icon → Settings
2. Or navigate to Settings page
3. Select desired category
4. Make changes
5. Save automatically

---

## Deleting Account

### Important Warnings ⚠️

**This action is PERMANENT:**
- ❌ Cannot be undone
- ❌ All data deleted immediately
- ❌ Items and outfits removed
- ❌ Personal models deleted
- ❌ Cannot restore account

### Deletion Steps

1. Go to Settings → Advanced
2. Scroll to "Danger Zone"
3. Click "Delete Account"
4. Confirm username (extra verification)
5. Confirm deletion
6. Account deleted immediately

### Before Deleting

- 📸 **Download images** if you want to keep them
- 📋 **Export data** (if available)
- 💾 **Note item information** elsewhere
- ⏰ **Wait before deciding** - this is permanent

---

## Account Security

### Best Practices

✅ **Do:**
- Use strong, unique passwords
- Change password regularly
- Logout on shared computers
- Use HTTPS in production (browser shows 🔒)
- Clear browser cache after logout

❌ **Don't:**
- Share password with anyone
- Use same password on multiple sites
- Logout and forget (logout actively)
- Use public WiFi without VPN
- Login on untrusted computers

### Suspicious Activity

If you notice unusual activity:
1. **Change password immediately**
2. **Logout all sessions**
3. **Contact administrator**
4. **Monitor account activity**

---

## Two-Factor Authentication (Future)

### Planned Feature

**Coming in future version:**
- Login verification via phone
- Additional security layer
- Optional backup codes

### Benefits

- Extra protection against password theft
- Confirms it's really you logging in
- Can be disabled if needed

---

## Troubleshooting

### Can't Login

**Check:**
1. Username spelled correctly (case-sensitive)
2. Caps Lock is off
3. Password is correct
4. Account exists (try registering)
5. Try clearing browser cache

**If still failing:**
1. Check application is running
2. Try restarting application
3. Check internet connection (if remote)

---

### Can't Change Password

**Check:**
1. Current password entered correctly
2. New password meets requirements
3. Password confirmation matches

**If still failing:**
1. Logout and login again
2. Restart application
3. Try again

---

### Account Locked (Future)

**Not currently implemented**, but planned:
- Account locks after multiple failed login attempts
- Can unlock via email reset
- Contact administrator to unlock

---

## Getting Help

### Support Resources

- 📖 See [User Guide](../user-guide/) for features
- 🐛 Report bugs to administrator
- ❓ See [FAQ](../troubleshooting/faq.md)
- 🔧 Check [Troubleshooting](../troubleshooting/common-issues.md)

---

## Next Steps

- Learn about [Wardrobe Management](wardrobe.md)
- Explore [Managing Items](items.md)
- See [Generating Outfits](outfits.md)
