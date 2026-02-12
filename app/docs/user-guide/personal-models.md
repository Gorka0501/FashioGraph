# User Guide - Personal Models

Understanding and managing your personal AI model.

## What is a Personal Model?

A **personal model** is an AI (neural network) trained specifically on YOUR preferences. It:

- 🧠 Learns from outfit ratings you provide
- 📊 Improves recommendations over time
- 👤 Is unique to you (not shared)
- 💾 Stored on your device
- 🔄 Updates automatically

### How It Works

```
Step 1: You use the app
  ↓
Step 2: You rate outfits
  ↓
Step 3: After 10 ratings:
  ├─ System creates personal model
  ├─ Trains on your preferences
  ├─ Saves to your device
  └─ Ready to use!
  ↓
Step 4: Next outfit generation
  ├─ Uses personal model
  ├─ Much better recommendations!
  └─ Matches YOUR taste
```

---

## Personal vs Base Model

### Base Model

**Definition:** Pre-trained, shared model for all users

**Features:**
- Generic outfit compatibility scoring
- Works for everyone
- No personalization
- Consistent baseline
- Available immediately

**Output:**
- Reasonable outfit suggestions
- Doesn't know your preferences
- Same for all users

### Personal Model

**Definition:** Trained on YOUR individual preferences

**Features:**
- Customized to your taste
- Learns from your ratings
- Improves over time
- Unique to you
- Created after 10 ratings

**Output:**
- Personalized recommendations
- Matches YOUR style
- Better accuracy

### Comparison Example

**Same outfit presented to two users:**

```
User A (Base Model):
- Compatibility: 3.5 stars (generic score)

User A (Personal Model):
- Compatibility: 4.8 stars (YOU love this combo!)

User B (Personal Model):
- Compatibility: 2.1 stars (NOT their style)
```

---

## Creating Your Personal Model

### Training Requirements

**To trigger auto-training, you need:**

✅ **10 rated outfits** - Core requirement  
✅ **3+ items in wardrobe** - Minimum diversity  
✅ **At least 1 outfit per day** - Spread over time (optional)  

### Timeline Example

```
Day 1:  Rate outfit 1 → Total: 1
Day 2:  Rate outfit 2 → Total: 2
Day 3:  Rate outfit 3 → Total: 3
Day 4:  Rate outfit 4 → Total: 4
Day 5:  Rate outfit 5 → Total: 5
        Rating outfit 6 → Total: 6
Day 6:  Rate outfit 7 → Total: 7
        Rate outfit 8 → Total: 8
Day 7:  Rate outfit 9 → Total: 9
        Rate outfit 10 → TRAINING TRIGGERED!
        ├─ System trains model
        ├─ Saves personal model
        └─ Counter resets

Day 8:  Outfit 11 uses personal model!
        Much better recommendations!
```

### Training Process

**What Happens During Training:**

1. **Data Collection** (1 second)
   - Gather your 10 ratings
   - Extract item features
   - Prepare training data

2. **Model Training** (3-5 seconds)
   - Neural network learns patterns
   - Adjusts weights to match your preferences
   - Runs multiple iterations
   - Validates on test data

3. **Model Saving** (1 second)
   - Saves trained model to device
   - Creates backup of previous version
   - Registers training completion

4. **Ready to Use** (Immediate)
   - Next outfit uses personal model
   - Rating counter resets to 0
   - Cycle can repeat

**Total Time:** 5-10 seconds (happens automatically)

---

## Monitoring Your Model

### Checking Model Status

**How to View:**
1. Click "Settings" ⚙️
2. Select "Model Status" or "AI Training"
3. View current status:

**Status Display Shows:**

```
Personal Model Status:
├─ Exists: Yes
├─ Created: January 2, 2024
├─ Training Count: 3
├─ Current Accuracy: 89%
├─ Last Updated: 5 minutes ago
│
Training Progress:
├─ Ratings Processed: 7 / 10
├─ Progress: ████████░ 70%
├─ Next Training: 3 ratings away
│
Next Training Triggers:
└─ When rating reaches 10
```

### Understanding Accuracy

**What is "Accuracy"?**
- How often model correctly predicts your preferences
- 0-100% scale
- Higher = better predictions

**Example:**
- Model predicts you'll rate outfit 4 stars
- You rate it 4-5 stars
- Prediction was accurate ✅

**Improving Accuracy:**
✅ Rate more outfits (need 10 minimum)  
✅ Rate honestly, not randomly  
✅ Provide diverse ratings  
✅ Add comments/notes  

---

## Training History

### Viewing Past Training

**Access Training History:**
1. Settings ⚙️
2. "Model Status" → "Training History"
3. See all past trainings

**Training History Shows:**

```
Training Session 1
├─ Date: January 2, 2024
├─ Ratings Used: 10
├─ Accuracy: 87%
├─ Improvement: +3%
└─ Time: 6 seconds

Training Session 2
├─ Date: January 12, 2024
├─ Ratings Used: 10
├─ Accuracy: 89%
├─ Improvement: +2%
└─ Time: 5 seconds

Training Session 3
├─ Date: January 22, 2024
├─ Ratings Used: 10
├─ Accuracy: 91%
├─ Improvement: +2%
└─ Time: 5 seconds
```

### Tracking Progress

**Typical Improvement Curve:**

```
Accuracy Over Time
│
95% │                  ╱─
    │              ╱──╯
90% │          ╱╯
    │      ╱╯
85% │  ╱╯
    │
80% └─────────────────────
    Training 1 2 3 4 5
```

- First training: Biggest jump (learning baseline)
- Subsequent: Smaller gains (refinement)
- Usually plateaus around 88-94%

---

## Resetting Your Model

### When to Reset

**Consider reset if:**
- Style has changed significantly
- Personal model not improving
- Major wardrobe overhaul
- Moving to new climate/location
- Starting fresh approach

### How to Reset

1. Settings ⚙️
2. "Model Status" → "Advanced"
3. Click "Reset Personal Model"
4. Confirm deletion
5. Model deleted

**After Reset:**
- ✅ Starts fresh with base model
- ✅ Counter resets to 0
- ✅ Training history cleared
- ✅ Ready for new training cycle

⚠️ **Note:** Deletion is permanent. History cannot be recovered.

---

## Improving Your Model

### Best Practices for Training

**Rating Quality:**
✅ Rate based on YOUR genuine preference  
✅ Consider "Would I actually wear this?"  
✅ Be consistent (don't rate randomly)  
✅ Provide mix of ratings (not all 5s)  
✅ Add notes when helpful  

**Content Diversity:**
✅ Rate outfits across different occasions  
✅ Try casual, formal, work, etc.  
✅ Mix different item combinations  
✅ Include various seasons/colors  

**Feedback Consistency:**
✅ Similar styles = similar ratings  
✅ Different styles = different ratings  
✅ Learn your own patterns  
✅ Be authentic, not experimental  

### What Hurts Training

❌ Rating all outfits the same (e.g., all 5s)  
❌ Random ratings (no pattern)  
❌ Not enough diversity  
❌ Changing preferences constantly  
❌ Insufficient items in wardrobe  

---

## Model Statistics

### Performance Metrics

**Accuracy**
- How well model predicts your ratings
- 0-100%
- Typical range: 80-95%
- Higher is better

**Loss**
- Technical error metric
- Lower is better
- Shows training quality
- Usually decreases with training

**Improvement**
- % increase vs previous version
- Typical: 1-3% per training
- First training may show larger jump
- Shows model learning

### Comparison with Base Model

**See How Personal Model Performs:**

1. Settings ⚙️
2. "Model Status" → "Compare Models"
3. View comparison:

```
Base Model (Generic):
├─ Accuracy: 82%
├─ Characteristics: Generic compatibility
└─ Note: Works for everyone

Personal Model (Your Model):
├─ Accuracy: 91%
├─ Characteristics: Your preferences
├─ Improvement: +9% better!
└─ Note: Custom trained
```

---

## Troubleshooting Model Issues

### Model Not Training

**Problem:** Reached 10 ratings but model didn't train

**Check:**
1. Have exactly 10+ rated outfits?
2. Wardrobe has 3+ items?
3. Items in different categories?
4. Auto-training enabled?

**Solutions:**
1. Rate more outfits manually
2. Add more items to wardrobe
3. Check model status in settings
4. Restart application

### Low Accuracy

**Problem:** Model accuracy is low (< 80%)

**Causes:**
1. Insufficient training samples
2. Inconsistent ratings
3. Wardrobe too small
4. Random rating patterns

**Solutions:**
1. Rate more outfits (aim for 50+)
2. Rate more consistently
3. Add diverse items
4. Be more deliberate with ratings

### Model Training Slow

**Normal Behavior:**
- First training: 5-10 seconds
- Subsequent: 3-5 seconds
- Happens automatically
- You can use app during training

**If taking longer:**
1. Check system resources (RAM, CPU)
2. Close other applications
3. Check internet connection
4. Restart application

### Wrong Recommendations

**Problem:** Personal model suggests bad outfits

**Causes:**
1. Not enough training data
2. Unclear rating patterns
3. Inconsistent preferences
4. Wardrobe needs improvement

**Solutions:**
1. Rate more outfits (build history)
2. Be consistent in ratings
3. Provide clear feedback
4. Improve item metadata
5. Reset and start over if needed

---

## Advanced Features (Future)

**Planned Enhancements:**
- 📊 Detailed model analytics
- 🎯 Style preference visualization
- 🔀 Model comparison with other users (anonymized)
- ⚙️ Fine-tuning controls
- 🔄 Incremental learning display
- 📈 Accuracy projection

---

## Model Privacy & Storage

### Where is Model Stored?

**Location:** `~/.fashion_wardrobe_app/models/personal/{username}/`

**Files:**
- `hgnn_base.pth` - Initial model copy
- `hgnn_v1.pth` - First training
- `hgnn_v2.pth` - Second training
- `hgnn_v3.pth` - Latest version

### Privacy & Security

✅ **Your data stays on your device**  
✅ Model never sent to server  
✅ Fully private and personal  
✅ No tracking or monitoring  
✅ Delete anytime via reset  

---

## Next Steps

- Learn [Rating Outfits](outfits.md#rating-outfits)
- Explore [Outfit Generation](outfits.md)
- Check [Model Status](personal-models.md#checking-model-status)
