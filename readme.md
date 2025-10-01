# mikroblogusers

Asynchroniczny pobieracz profili z JBZD, zapis do SQLite z batchowym commitowaniem,
checkpointingiem, dynamicznym throttlingiem i live statystykami.

Uruchamiany ręcznie lub automatycznie przez GitHub Actions. SQLite (`profiles.db`) jest
zapisany jako artifact po każdym uruchomieniu workflow.
