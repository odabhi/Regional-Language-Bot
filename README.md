# Hindi Moderator Bot with Broadcast Feature 🤖

A powerful Telegram bot that moderates Hindi language usage in groups and allows broadcasting messages to all groups.

## Features ✨

- **Hindi Detection**: Detects both Devanagari script and Romanized Hindi words
- **Link Prevention**: Automatically blocks URLs and Telegram links
- **Warning System**: 3 warnings then 15-minute mute for Hindi usage
- **Broadcast Feature**: Send messages to all groups at once
- **Admin Tools**: Approve/disapprove users, view approved list
- **Auto Group Tracking**: Automatically tracks all groups bot is added to

## Commands 🎯

### For Everyone:
- `/start` - Start the bot
- `/ocr` - Check if bot is alive

### For Group Admins:
- `/abhiloveu` - Approve a user (reply to user's message)
- `/abhihateu` - Disapprove a user (reply to user's message)  
- `/abhilovelist` - Show all approved users

### For Bot Owner (User ID: 814xxxxxx):
- `/broadcast` - Send message to all groups
- `/listchats` - List all groups where bot is added

## Setup 🚀

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/hindi-moderator-bot.git
   cd hindi-moderator-bot
