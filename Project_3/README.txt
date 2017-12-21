1. Install program
got to: http://bioinfo.lifl.fr/RNA/sortmerna/ 
download: Version 2.1 binary for Linux 64-bit (compiled using GCC multi-threading supported)
scp -i ~/.ssh/Bioinfo_US_east_1.pem ~/Downloads/sortmerna-2.1-linux-64-multithread.tar.gz ubuntu@34.226.169.108:transcriptome/rnr/
tar -xvf sortmerna-2.1-linux-64-multithread.tar.gz
PATH=$PATH:/home/ubuntu/transcriptome/rnr/sortmerna-2.1b/
export PATH

2. Get test files
- select sampleid, g.intsampleid, symbol, s.created, sum(readcount) from sample_gene_expression g, sample s where g.intsampleid=s.intsampleid and symbol like 'RNR%' and g.intsampleid in (2078,2079,3898,3899,244,214,212) group by 1, 2, 3, 4 order by 4;
- pick 252790179418
- Amazon s3 > viomelabresults > inputs > search 252790179418
aws s3 cp s3://viomelabresults/inputs/252790179418/252790179418_S87_R1_001.fastq.gz .
aws s3 cp s3://viomelabresults/inputs/252790179418/252790179418_S87_R2_001.fastq.gz .
aws s3 cp s3://viomelabresults/outputs/252790179418/252790179418.QC.1.3.tar.gz .
gunzip *.gz

3. Get rnr probes
(open xls doc in googlesheet so that you can download it as a .csv then use) 
awk -F "," '{print $1,$2}' HBE_RNR_probes.csv | grep 'HBE' | awk -F "/" '{print $1}' | awk '{print ">"$1"\n"$2}' > HBE_RNR_probes.fasta
awk -F "," '{print $1,$2}' HBF_RNR_probes.csv | grep -v '#'| grep -v 'Probe' | awk -F "/" '{print $1}' | awk '{print ">"$1"\n"$2}' > HBF_RNR_probes.fasta
scp -i ~/.ssh/Bioinfo_US_east_1.pem ~/Desktop/*.fasta ubuntu@34.226.169.108:transcriptome/rnr/

4. Index rRNA database -- using all their files as well as our own two
indexdb_rna --ref rRNA_databases/silva-bac-16s-id90.fasta,index/silva-bac-16s:rRNA_databases/silva-bac-23s-id98.fasta,index/silva-bac-23s:rRNA_databases/silva-arc-16s-id95.fasta,index/silva-arc-16s:rRNA_databases/silva-arc-23s-id98.fasta,index/silva-arc-23s:rRNA_databases/silva-euk-18s-id95.fasta,index/silva-euk-18s:rRNA_databases/silva-euk-28s-id98.fasta,index/silva-euk-28s:rRNA_databases/rfam-5.8s-database-id98.fasta,index/rfam-5.8s:rRNA_databases/rfam-5s-database-id98.fasta,index/rfam-5s:../HBE_RNR_probes.fasta,index/HBE:../HBF_RNR_probes.fasta,index/HBF

5. Merge PE reads
sortmerna-2.1b/scripts/merge-paired-reads.sh 252790179418_S87_R1_001.fastq 252790179418_S87_R2_001.fastq 252790179418_S87_merged.fastq

6.Map fastq against RNR reads and filter out
REFDB=$REFDB"rRNA_databases/silva-bac-16s-id90.fasta,index/silva-bac-16s:rRNA_databases/silva-bac-23s-id98.fasta,index/silva-bac-23s:rRNA_databases/silva-arc-16s-id95.fasta,index/silva-arc-16s:rRNA_databases/silva-arc-23s-id98.fasta,index/silva-arc-23s:rRNA_databases/silva-euk-18s-id95.fasta,index/silva-euk-18s:rRNA_databases/silva-euk-28s-id98.fasta,index/silva-euk-28s:rRNA_databases/rfam-5.8s-database-id98.fasta,index/rfam-5.8s:rRNA_databases/rfam-5s-database-id98.fasta,index/rfam-5s:../HBE_RNR_probes.fasta,index/HBE:../HBF_RNR_probes.fasta,index/HBF

sortmerna --ref $REFDB --reads ../252790179418_S87_merged.fastq --paired_in -a 16 --log --fastx --aligned 252790179418_rRNA.out --other 252790179418_sortmerna.fasta
 
#outputs:
-rw-rw-r-- 1 ubuntu ubuntu 142M Dec 19 20:33 252790179418_rRNA.out.fastq
-rw-rw-r-- 1 ubuntu ubuntu 3.7K Dec 19 20:33 252790179418_rRNA.out.log
-rw-rw-r-- 1 ubuntu ubuntu 1.5G Dec 19 20:33 252790179418_sortmerna.fastq

7. Map fastq again ONLY OUR DB and filter out
OURDB=$OURDB"../HBE_RNR_probes.fasta,index/HBE:../HBF_RNR_probes.fasta,index/HBF"
sortmerna --ref $OURDB --reads ../files_raw/252790179418_S87_merged.fastq --paired_in -a 16 --log --fastx --aligned ../files_sortmerna_ourdb/252790179418_rRNA_ourdb.out --other ../files_sortmerna_ourdb/252790179418_sortmerna_ourdb

#ouputs
-rw-rw-r-- 1 ubuntu ubuntu 100M Dec 19 21:23 252790179418_rRNA_ourdb.out.fastq
-rw-rw-r-- 1 ubuntu ubuntu 1.4K Dec 19 21:23 252790179418_rRNA_ourdb.out.log
-rw-rw-r-- 1 ubuntu ubuntu 1.6G Dec 19 21:23 252790179418_sortmerna_ourdb.fastq

8. For host_removal.pl program
-make one large fasta file of all rnr reads
cat sortmerna-2.1b/rRNA_databases/*.fasta HBE_RNR_probes.fasta HBF_RNR_probes.fasta> ref.fasta

time perl host_reads_removal_by_mapping.pl -ref ref.fasta -p 252790179418_S87_R1_001.fastq 252790179418_S87_R2_001.fastq -o /home/ubuntu/transcriptome/rnr/files_hostremoval -prefix host_removal

-merge PE files for fastqc
../../sortmerna-2.1b/scripts/merge-paired-reads.sh ../../files_hostremoval/host_removal.1.fastq ../../files_hostremoval/host_removal.2.fastq host_removal_merged.fastq

#outputs:
-rw-rw-rw- 1 ubuntu ubuntu 732M Dec 19 21:00 host_removal.1.fastq
-rw-rw-rw- 1 ubuntu ubuntu 727M Dec 19 21:00 host_removal.2.fastq
-rw-rw-r-- 1 ubuntu ubuntu 1.4K Dec 19 21:01 host_removal.log
-rw-rw-rw- 1 ubuntu ubuntu  14K Dec 19 21:00 host_removal.mapping.log
-rw-rw-r-- 1 ubuntu ubuntu 1.5G Dec 19 21:13 host_removal_merged.fastq
-rw-rw-rw- 1 ubuntu ubuntu  364 Dec 19 21:00 host_removal.stats.txt
-rw-rw-rw- 1 ubuntu ubuntu 8.7M Dec 19 21:00 host_removal.unpaired.fastq
-rw-rw-r-- 1 ubuntu ubuntu  73M Dec 19 20:09 ref.fasta
-rw-rw-rw- 1 ubuntu ubuntu  20M Dec 19 20:55 ref.fasta.amb
-rw-rw-rw- 1 ubuntu ubuntu 7.1M Dec 19 20:55 ref.fasta.ann
-rw-rw-rw- 1 ubuntu ubuntu  68M Dec 19 20:55 ref.fasta.bwt
-rw-rw-rw- 1 ubuntu ubuntu  17M Dec 19 20:55 ref.fasta.pac
-rw-rw-rw- 1 ubuntu ubuntu  34M Dec 19 20:55 ref.fasta.sa


9. Run Fastqc on all attemps
fastqc ../../252790179418_S87_merged.fastq -t 8 -o /home/ubuntu/transcriptome/rnr/qc/initial > log
fastqc ../../files_sortmerna/252790179418_sortmerna.fastq -t 8 -o /home/ubuntu/transcriptome/rnr/qc/sortmerna > log
fastqc ../../files_hostremoval/host_removal_merged.fastq -t 8 -o /home/ubuntu/transcriptome/rnr/qc/host_removal > log
fastqc ../../files_sortmerna_ourdb/252790179418_sortmerna_ourdb.fastq -t 8 -o /home/ubuntu/transcriptome/rnr/qc/sortmerna_ourprobes > log

10. Visualize on local computer
scp -r -i ~/.ssh/Bioinfo_US_east_1.pem ubuntu@34.226.169.108:/home/ubuntu/transcriptome/rnr/qc /Users/aseveritt/Desktop

11. Realize the data looks weird and ask?
    -11a. what does "standard" data look like?
    -11b. what would it take to transform this data into a good quality?
    -11c. what does current output look like?
    -11d. what do other samples look like?

11a. Get Standard data to compare against:
    https://www.ncbi.nlm.nih.gov/sra/SRX3408808[accn]
    /Users/aseveritt/Desktop/sratoolkit.2.8.2-1-mac64/bin/fastq-dump -A SRR6308425
    scp -i ~/.ssh/Bioinfo_US_east_1.pem ACCESSION_SRR6308425.fastq.gz ubuntu@34.226.169.108:transcriptome/rnr/qc/accesion
    
11b. Transform original sample:
    13a. remove sequence < 50bp
    13b. remove sequence "NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN" and "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGN"
wget http://www.usadellab.org/cms/uploads/supplementary/Trimmomatic/Trimmomatic-0.36.zip
unzip Trimmomatic-0.36.zip
cp 252790179418_sortmerna.fastq ../files_trimmomatic/
../sortmerna-2.1b/scripts/unmerge-paired-reads.sh 252790179418_sortmerna.fastq 252790179418_sortmerna.forward.fastq 252790179418_sortmerna.reverse.fastq
java -jar ../Trimmomatic-0.36/trimmomatic-0.36.jar PE -threads 8 252790179418_sortmerna.forward.fastq 252790179418_sortmerna.reverse.fastq 252790179418_sortmerna.forward.trim.fastq 252790179418_sortmerna.reverse.trim.fastq 252790179418_sortmerna.forward.unpaired.fastq 252790179418_sortmerna.reverse.unpaired.fastq LEADING:3 TRAILING:3 MINLEN:50
    #difference
    #ubuntu@ip-192-168-2-216:~/transcriptome/rnr/files_trimmomatic$ grep "@" 252790179418_sortmerna.forward.fastq | wc -l
    #2282219
    #ubuntu@ip-192-168-2-216:~/transcriptome/rnr/files_trimmomatic$ grep "@" 252790179418_sortmerna.forward.trim.fastq | wc -l
    #2117921
    
../sortmerna-2.1b/scripts/merge-paired-reads.sh 252790179418_sortmerna.forward.trim.fastq 252790179418_sortmerna.reverse.trim.fastq 252790179418_sortmerna.merged.trim.fastq
fastqc 252790179418_sortmerna.merged.trim.fastq -t 8 > log

11c. What does the current output look like?
    s3 cp s3://viomelabresults/outputs/252790179418/252790179418.QC.1.3.tar.gz ./
    ubuntu@ip-192-168-2-216:~/transcriptome/rnr/qc/curr_output/252790179418/QcReads$ cp QC.1.trimmed.fastq ../../
    ../../sortmerna-2.1b/scripts/merge-paired-reads.sh QC.1.trimmed.fastq QC.2.trimmed.fastq QC.merged.trimmed.fastq
    fastqc QC.merged.trimmed.fastq -t 8 -o >log


11d. Grab another sample - repeat all steps
Randomly choose RD_1187
aws s3 cp s3://viomelabresults/inputs/RD_1187/RD_1187_S13_R1_001.fastq.gz ./
aws s3 cp s3://viomelabresults/inputs/RD_1187/RD_1187_S13_R2_001.fastq.gz ./
aws s3 cp s3://viomelabresults/outputs/RD_1187/RD_1187.QC.1.3.tar.gz ./

../sortmerna-2.1b/scripts/merge-paired-reads.sh RD_1187_S13_R1_001.fastq RD_1187_S13_R2_001.fastq RD_1187_S13_merged.fastq
fastqc ../../files_raw_RD_1187/RD_1187_S13_merged.fastq -t 8 -o /home/ubuntu/transcriptome/rnr/qc/RD_1187 > log


