import os,sys,argparse

def mergefastq(in1,in2,od,smrna_dir):
    cmd = '{}/scripts/merge-paired-reads.sh {} {} {}/interleaved.fastq'.format(smrna_dir,in1,in2,od)
    print("COMMAND:", cmd)
    os.system( cmd )

def runsortmerna(od,smrna_dir,probedb,threads):
    a = '{}/rRNA_databases'.format(smrna_dir)
    b = '{}/index'.format(smrna_dir)
    if (probedb): #only viome
        REF = '{}/HBE_RNR_probes.fasta,{}/HBE:{}/HBF_RNR_probes.fasta,{}/HBF'.format(a,b,a,b)
    else:
        REF = '{}/HBE_RNR_probes.fasta,{}/HBE:{}/HBF_RNR_probes.fasta,{}/HBF:{}/silva-bac-16s-id90.fasta,{}/silva-bac-16s:{}/silva-bac-23s-id98.fasta,{}/silva-bac-23s:{}/silva-arc-16s-id95.fasta,{}/silva-arc-16s:{}/silva-arc-23s-id98.fasta,{}/silva-arc-23s:{}/silva-euk-18s-id95.fasta,{}/silva-euk-18s:{}/silva-euk-28s-id98.fasta,{}/silva-euk-28s:{}/rfam-5.8s-database-id98.fasta,{}/rfam-5.8s:{}/rfam-5s-database-id98.fasta,{}/rfam-5s'.format(a,b,a,b,a,b,a,b,a,b,a,b,a,b,a,b,a,b,a,b)

    cmd = '{}/sortmerna --ref {} --reads {}/interleaved.fastq --paired_in -a {} --log --fastx --aligned {}/sortmerna.RNR.out --other {}/sortmerna.out'.format(smrna_dir, REF, od, threads, od, od)
    print("COMMAND:", cmd)
    os.system(cmd)

def runfastqc(threads,od,fastqc_only):
    if (fastqc_only):
        cmd = 'fastqc {}/interleaved.fastq -t {} -o {}'.format(od,threads,od)
    else:
        cmd = 'fastqc {}/sortmerna.out.fastq -t {} -o {}'.format(od,threads,od)

    print("COMMAND:",cmd)
    os.system(cmd)

def main(in1,in2,out1,threads,smrna_path,probedb,smrna_only,fastqc_only):
    print("....merging fastqc files")
    mergefastq(in1, in2, out1,smrna_path)
    if (smrna_only):
        print ("....running SortMeRNA")
        runsortmerna(out1,smrna_path,probedb,threads)
    elif (fastqc_only):
        print(".....running FastQC")
        runfastqc(threads,out1,fastqc_only)
    else:
        print ("....running SortMeRNA")
        runsortmerna(out1,smrna_path,probedb,threads)
        print(".....running FastQC")
        runfastqc(threads,out1,fastqc_only)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser = argparse.ArgumentParser(description='Run Sortmerna and Fastqc',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # generic parameters

    parser.add_argument('-i1',help = "read 1 fastq", action = "store", dest="in1", required = True)
    parser.add_argument('-i2',help = "read 2 fastq", action = "store", dest="in2", required = True)
    parser.add_argument('-od', help='output directory', action="store", dest='out1', default='.', required=True)
    parser.add_argument('-t', help = "threads to use", action= "store", dest = "threads", default=8)
    # SortMeRNA
    parser.add_argument('-path', help = "Path to SortMeRNA", action ="store", dest="smrna_path", default= "/home/ubuntu/transcriptome/rnr/sortmerna-2.1b")
    parser.add_argument('-vp', help ="Use only Viome RNR Probes", action = "store", dest="probedb", default=False)
    parser.add_argument('-smrna', help ="Only run SortMeRNA", action = "store", dest = "smrna_only", default=False)
    #FastQC
    parser.add_argument('-fastqc', help ="Only run FastQC", action = "store", dest = "fastqc_only", default=False)
    args = parser.parse_args()

    
    main(args.in1, args.in2, args.out1, args.threads, args.smrna_path, args.probedb, args.smrna_only,args.fastqc_only)
