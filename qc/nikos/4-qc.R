
library(dplyr)
library(ggplot2)
library(patchwork)

setwd("/data/hemberg/nikos/hubmap/project/stella-folders/")
options(scipen = 999, width = 200)

df = as.data.frame(data.table::fread("all-decont-meta.csv"))
tissues.available = unique(df$tissue)


df$nFeature_RNA = df$n_genes_by_counts
df$nCount_RNA = df$total_counts
df$percent.mt = df$pct_counts_mito
df$percent.ribo = df$pct_counts_ribo
df$percent.er = df$pct_counts_ribo
df$percent.malat1 = df$pct_counts_ribo
df$doublet = df$pred_dbl == "True"
df$doublet[df$doublet & (df$doublet_score < 0.1)] = FALSE
df$doublet[!df$doublet & (df$doublet_score > 0.35)] = TRUE
df$ambient = df$pred_dbl != "nan"


whitelist = df$cell_id[df$ambient][df$decont_rate[df$ambient] < 0.5]
white.mask = df$cell_id %in% whitelist
df$ambient = df$ambient & white.mask

## df[!is.na(df$decont_rate),]  %>% group_by(tissue, sample_id) %>% summarize(rate = sum(decont_rate > 0.5)/n(), cells = n()) %>% arrange(-rate)


### Identify what QC has already been done to cells
df %>%group_by(tissue) %>% summarize(cells = n(),
                                     min.counts = min(nCount_RNA), min.features = min(nFeature_RNA), min.mito=min(percent.mt), min.ribo = min(percent.ribo),
                                     max.counts = max(nCount_RNA), max.features = max(nFeature_RNA), max.mito=max(percent.mt), max.ribo = max(percent.ribo),
                                     median.counts = median(nCount_RNA), median.features = median(nFeature_RNA),
                                     median.mito = median(percent.mt), median.ribo = median(percent.ribo)) %>% write.csv("pre-existing-qc.csv")


### Level 1
df$mask.l1 = with(df, !(nCount_RNA > 50000 | nCount_RNA < 500 | nFeature_RNA < 200))
df %>%group_by(tissue) %>% summarize(cells=n(), low.quality = sum(!mask.l1), pass.qc = sum(mask.l1)/n()) %>% arrange(pass.qc) %>% write.csv("tissues-qc-level1.csv")

### Level 2 QC - SAMPLE LEVEL
## Sample level statistics
quantile.10 =  function(x){as.numeric(quantile(x, 0.10))}
quantile.90 =  function(x){as.numeric(quantile(x, 0.90))}

stats.df = df %>% group_by(tissue, sample_id) %>%
    summarize(cells = n(), cells.qc.l1 = sum(mask.l1), cell.prop.l1 = sum(mask.l1)/n(), ambient.prop = sum(ambient)/n(),
              counts = median(nCount_RNA), counts.90 = quantile.90(nCount_RNA), counts.10 = quantile.10(nCount_RNA),
              features = median(nFeature_RNA), features.90 = quantile.90(nFeature_RNA), features.10 = quantile.10(nFeature_RNA),
              doublet.prop = sum(doublet)/sum(ambient), doublet.score = sum(doublet_score[ambient])/sum(ambient),
              mito = median(percent.mt), mito.90 = quantile.90(percent.mt), mito.10 = quantile.10(percent.mt),              
              ribo = median(percent.ribo), ribo.90 = quantile.90(percent.ribo), ribo.10 = quantile.10(percent.ribo),
              er = median(percent.er), er.90 = quantile.90(percent.er), er.10 = quantile.10(percent.er),
              malat1 = median(percent.malat1), malat1.90 = quantile.90(percent.malat1), malat1.10 = quantile.10(percent.malat1))
                                                                           
stats.df %>% select(doublet.prop, doublet.score)

write.csv(stats.df, "qc-sample-level-report.csv")



samples.blacklist = c(
    ## Intestine high rate of l1 failing
    "B006-A-101",
    "B006-A-201",
    "B006-A-001",
    "B009-A-401",
    ## Uterus outliers in the mitochondria
    "13-74",
    "13-94",
    ## Kidney more than 5% mitochondria (median)
    "PA1",
    "KM162",
    "KC147",
    ## High ribo
    "KM152",
    ## Heart median high mito  more than 11%
    "LV5",
    "RA5",
    "RV5",
    "SA5",
    ## Bone marrow
    "D3_arcv1",
    ## Uterus bad samples failing % in l1
    "11-128",
    "9-UPBSEL",
    "13-101")







df$sample.l2 = !(df$sample_id %in% samples.blacklist)

df$mask.l2 = df$mask & df$sample.l2






### Level 3 QC - Enforce feature and gene feature on decontX min counts and features

df$l3.filter = with(df, (doublet | ambient))
df$mask.l3 = with(df, mask.l2 & l3.filter)



### Level 4 QC - cell level mito % and ribo %

ribo.filter = list(
    'cervix' = 12,
    'fallopiantube' = 10,
    'IVD' = 35,
    'IVD2' = 35,
    'heart' = 10,
    'intestine' = 15,
    'kidney' = 17,
    'lung' = 10,
    'ovary' = 10,
    'placenta' = 2,
    'skin' = 60,
    'uterus' = 20,
    "bonemarrow" = 60,
    "bonemarrow2" = 10,
    "pancreas" = 5,
    "liver" = 5,
    "bronchus" = 5

)

mito.filter = list(
    'cervix' = 10,
    'fallopiantube' = 5,
    'IVD' = 5,
    'IVD2' = 5,
    'heart' = 17,
    'intestine' = 6,
    'kidney' = 20,
    'lung' = 15,
    'ovary' = 5,
    'placenta' = 3,
    'skin' = 12,
    'uterus' = 15,
    "bonemarrow" = 15,
    "bonemarrow2" = 20,
    "pancreas" = 5,
    "liver" = 5,
    "bronchus" = 7

)




df$bad.percent.ribo = FALSE
df$bad.percent.mt = FALSE

for (n in tissues.available) {
    message(n)
    filters = list(percent.mt = mito.filter, percent.ribo = ribo.filter)
    mask = df$tissue == n
    for(.cov in names(filters)){

        .cov.edit = paste0("bad.", .cov)
        df[mask,.cov.edit] = df[mask,.cov] > filters[[.cov]][[n]]
    }
}

df[df$mask.l3,] %>% group_by(tissue) %>% summarize(cells = n(), perc.bad = (sum(bad.percent.ribo | bad.percent.mt)/n())*100 , ribo = sum(bad.percent.ribo), mito = sum(bad.percent.mt)) %>% write.csv("qc-l4.csv")



df$mask.l4 = with(df, mask.l3 & !(bad.percent.ribo | bad.percent.ribo))

df %>% group_by(tissue,sample_id) %>%
    summarize(cells = n(),
              counts = median(nCount_RNA),
              features = median(nFeature_RNA),
              ribo = median(percent.ribo),
              mito = median(percent.mt),
              er = median(percent.er),
              malat1 = median(percent.malat1),
              counts = median(nCount_RNA),
              l1.qc = sum(mask), l2.qc = sum(mask.l2), l3.qc = sum(mask.l3), l4.qc = sum(mask.l4), perc.removed = (1 - (sum(mask.l4)/n()))*100) %>%
                                                                                 write.csv("qc-all-sample_id.csv")


df %>% group_by(tissue) %>%
    summarize(cells = n(),
              sample_ides = n_distinct(sample_id),
              counts = median(nCount_RNA),
              features = median(nFeature_RNA),
              ribo = median(percent.ribo),
              mito = median(percent.mt),
              er = median(percent.er),
              malat1 = median(percent.malat1),
              counts = median(nCount_RNA),
              l1.qc = sum(mask), l2.qc = sum(mask.l2), l3.qc = sum(mask.l3), l4.qc = sum(mask.l4),
              perc.removed = (1 - (sum(mask.l4)/n()))*100) %>%
write.csv("qc-all-tissue.csv")


### Export final dataframe
write.csv(df, "metadata-filtered.csv")

## Useful metric to see if we remove consistently specific cell types

df %>% group_by(tissue) %>% mutate(low.quality.tissue.prop = sum(!mask.l4)/n()) %>%
    group_by(tissue, tissue_cell_type) %>%
    summarize(cells=n(),
              low.quality = sum(!mask.l4),
              pass.qc = sum(mask.l4)/n(),
              tissue.lfc=log2((sum(!mask.l4)/n())/mean(low.quality.tissue.prop))) %>%
    filter(low.quality > 100) %>%
    arrange(-abs(tissue.lfc)) %>% write.csv("cell-final-qc-celltype-enrichment.csv")





