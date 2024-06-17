if [ -z $UPSTREAM_REPO ]
then
  echo "Cloning main Repository"
  git clone https://github.com/Deendayal423/Deendayal_dhakad.git /Deendayal_dhakad 
else
  echo "Cloning Custom Repo from $UPSTREAM_REPO "
  git clone $UPSTREAM_REPO /Deendayal_dhakad
fi
cd /Deendayal_dhakad
pip3 install -U -r requirements.txt
echo "Starting Deendayal_dhakad...."
python3 bot.py
