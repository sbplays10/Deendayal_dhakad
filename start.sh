if [ -z $UPSTREAM_REPO ]
then
  echo "Cloning main Repository"
  git clone https://github.com/Deendayal423/Super-Filter-bot.git /Super-Filter-bot 
else
  echo "Cloning Custom Repo from $UPSTREAM_REPO "
  git clone $UPSTREAM_REPO /Super-Filter-bot
fi
cd /Super-Filter-bot
pip3 install -U -r requirements.txt
echo "Starting Super-Filter-bot...."
python3 bot.py
