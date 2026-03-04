SECONDS=0
while true; do
  printf "\rElapsed: %02d:%02d:%02d" $((SECONDS/3600)) $((SECONDS%3600/60)) $((SECONDS%60))
  sleep 1
done
