# 🔄 Alternative: Regenerate Consumer Secret

If the [Show] button isn't working, you can **regenerate** the Consumer Secret to get a new one you can see.

---

## ✅ Step 1: Go to Your App

```
Setup → Manage apps → Connected apps → DataGuardian Pro
```

---

## ✅ Step 2: Look for "Manage Consumer Details"

Scroll down in the app details. Look for:

```
CONSUMER DETAILS section
┌──────────────────────────────────────┐
│ Consumer Key                         │
│ 3MVG9d8._XXXXXXXX...                 │
│                                      │
│ Consumer Secret                      │
│ ••••••••••••••••••                   │
│                                      │
│ [Manage Consumer Details]  ← CLICK  │
│ or                                   │
│ [Edit] or [Revoke]                   │
└──────────────────────────────────────┘
```

Click **[Manage Consumer Details]** or **[Edit]** button

---

## ✅ Step 3: Click "Rotate Consumer Secret"

In the management panel, look for:

```
Consumer Secret Management
┌──────────────────────────────────────┐
│ Current Secret (hidden)              │
│ ••••••••••••••••••                   │
│                                      │
│ [Rotate Consumer Secret]  ← CLICK   │
│ or                                   │
│ [Regenerate Secret]  ← CLICK         │
└──────────────────────────────────────┘
```

Click the **Rotate** or **Regenerate** button

---

## ✅ Step 4: Confirm Action

You'll see a confirmation popup:

```
⚠️ WARNING

Rotating the consumer secret will invalidate 
the current secret. New applications using 
the old secret will fail to authenticate.

Are you sure?

[Cancel]  [Rotate/Regenerate]
```

Click **[Rotate]** or **[Regenerate]**

---

## ✅ Step 5: NEW Secret Will Be Visible

After rotation, you'll see:

```
CONSUMER DETAILS (UPDATED)
┌──────────────────────────────────────┐
│ NEW Consumer Secret                  │
│ 9x8y7z6w5v4u3t2s1r0q9p8o7n6m5l4k3j  │
│                                      │
│ [Copy]  ← CLICK NOW!                 │
│                                      │
│ Last rotated: Nov 25, 2025           │
└──────────────────────────────────────┘
```

**Immediately click [Copy]** to save it!

---

## 🎯 Alternative: Direct Copy

If you see the new secret displayed (not hidden), you can:

1. **Triple-click** to select all the text
2. **Ctrl+C** (or **Cmd+C** on Mac) to copy
3. **Paste** into the Python script

---

## 📋 If There's No Rotate Button

Try these locations:

### Location 1: Under CONSUMER DETAILS
```
[View Consumer Details]  or  [Manage]
```

### Location 2: At Top of Page
Look for action buttons at the very top:
```
[Edit] [Delete] [Reset] [Revoke]
```

Click **[Edit]** or **[Reset]**

### Location 3: Three-Dot Menu
Look for **⋯** (three dots) menu:
```
⋯ [More Actions] → [Rotate Secret] or [Reset]
```

---

## 🚀 Once You Have New Secret

```bash
python GET_SALESFORCE_OAUTH_KEYS.py
```

Paste:
- **Consumer Key:** (the same one from before)
- **Consumer Secret:** (the NEW regenerated one)

---

## ⚠️ Important

- **Old secret won't work anymore** after rotation
- **New secret will work** - use this one in DataGuardian Pro
- **This is safe to do** - it's designed for this purpose

---

**Try looking for [Rotate Consumer Secret] or [Regenerate Secret] button now!** 🔄
