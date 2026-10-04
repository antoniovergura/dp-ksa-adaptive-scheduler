# Sorgenti e provenienza della campagna Mac del 26 settembre 2026

La campagna è un nuovo esperimento. I risultati originali del 20 settembre non vengono ricostruiti né sovrascritti.

- `provenienza.json`: elenco e hash dello snapshot, confronto con le sorgenti RTX e ambiente Python effettivo.
- `sorgenti_e_input.tar.gz`: sorgenti storiche del commit `8b770e0`, test e corpora pubblici o sintetici. Non contiene credenziali né il modello GGUF.
- `esegui.py`: launcher che verifica sorgenti, modello, corpora e provider prima dell’avvio. La copia estratta in `runtime/` è una directory di lavoro locale, esclusa da Git; modello e credenziali sono risorse esterne allo snapshot.
- `verifica_preliminare.json`: verifica dei 332 file storici disponibili e dei test sullo snapshot. Con accesso ai sensori, 186 test superati; il tentativo iniziale in ambiente ristretto aveva due fallimenti sui sensori indisponibili.
- `ambiente_runtime.json`: versioni effettive delle dipendenze e condizioni registrate all’avvio.
- `esecuzione.log`: avanzamento della campagna, senza chiavi.
- `grezzi_confronto_integrato.tar.gz`: i 623 file del manifest corrente, comprese le 600 richieste, più il manifest stesso.
- `ARCHIVIO_PUBBLICO.json`: dimensioni e hash SHA-256 dei due archivi pubblicati.

Il campo `git_commit` scritto dal runner nei metadata identifica il checkout che contieneva la copia di lavoro. Il commit dei sorgenti effettivamente eseguiti è `baseline_commit` in `provenienza.json`, verificabile tramite `source_hashes` nei metadata.

Il [protocollo](../../misurazioni/REPLICA_MAC_2026-09-26.md) documenta impostazioni e differenze degli ambienti. Il modello è Qwen2.5 0.5B Q4_K_M, verificato mediante lo stesso hash conservato nei metadata RTX. Per ripetere l’esperimento occorre scegliere una nuova directory e registrare la nuova data: il launcher impedisce di sovrascrivere o riprendere una campagna con un account di privacy azzerato.

Il [verificatore dei dati](../../scripts/verify_experiments.py) controlla grezzi, aggregati e snapshot senza inferenze. Gli archivi storici preservano percorsi e nomi registrati all’esecuzione; la documentazione corrente costituisce il punto di accesso per riprodurre l’analisi.
