library(dplyr)
library(ggplot2)
library(patchwork)
setwd("/data/hemberg/nikos/hubmap/project/stella-folders/")
options(scipen = 999, width = 200)

df = as.data.frame(data.table::fread("metadata-filtered.csv"))



#### Plotting


for (n in tissues.available) {
    message(n)
    tissue.df <- df %>% filter(tissue == n)
    for (.cov in c("percent.mt", "percent.ribo", "percent.er", "percent.malat1", "nCount_RNA", "nFeature_RNA"))
    {
        unique.sample_ides= length(unique(tissue.df$sample_id))
        g = ggplot(tissue.df, aes(x=.data[[.cov]])) + geom_histogram(bins = 200) + facet_wrap(~sample_id, ncol = 10)
        theme_classic()
        ggsave( paste0("figures/qc/dataset/tissue/",n,"/histo-", n,"_", .cov,".png"),
               height = (as.integer(unique.sample_ides/10)+1)*3, width = 20, create.dir=TRUE)
        ## ggsave(paste0("figures/qc/dataset/tissue/",n,"/histo-", n,"_", .cov,".png"))
    }
}


for (n in tissues.available) {
    message(n)
    .df <- subset(stats.df, tissue == n)
    if(nrow(.df) < 10){
        next
    }
    g = list()
    for (.cov in c("mito", "ribo", "malat1", "counts", "features"))
    {
        g[[.cov]] = ggplot(.df, aes(x=.data[[.cov]])) + geom_histogram() + theme_classic()
    }
    gall = Reduce(`+`, g)
    ggsave(paste0("figures/qc/tissues/histo-sample_id-", n,".png"), height = 10)
}


for (.cov in c("percent.mt", "percent.ribo", "percent.er", "nCount_RNA", "nFeature_RNA"))
{
    g = ggplot(df, aes(x=.data[[.cov]])) + geom_density(adjust = 1/5) + facet_wrap(~tissue, ncol = 6) + theme_classic()
    ggsave(paste0("figures/qc/density-","_", .cov,".png"), height = 14, width=21)
    g = ggplot(df, aes(x=.data[[.cov]])) + geom_histogram() + facet_wrap(~tissue, ncol = 6) + theme_classic()
    ggsave(paste0("figures/qc/histo-","_", .cov,".png"), height = 14, width=21)
}

g = ggplot(seu@meta.data, aes(x=.data[[.cov]])) + geom_histogram(bins = 200) + theme_classic()



### Scatter for samples



## Scatter plots per tissue facet
library(ggrepel)

scatter <- function(stats.df, x, y) {
    varmin= paste0(y,".10")
    varmax= paste0(y,".90")
    scatter.plot = ggplot(stats.df, aes(x=!!rlang::sym(x), y=!!rlang::sym(y), label=sample_id)) +
        geom_point()  +
        geom_label_repel(max.overlaps=2) +
        geom_errorbar(aes(ymin=.data[[varmin]], ymax=.data[[varmax]]), width=.2,
                 position=position_dodge(0.05)) +
        facet_wrap(~tissue) +
        geom_smooth(method = "lm", se = FALSE)

    ggsave(paste0("figures/qc/scatter-tissue_", x,"-", y,".png"), height = 20, width = 20)
}




scatter(stats.df, "counts","features")
scatter(stats.df, "counts","mito")
scatter(stats.df, "features","mito")
scatter(stats.df, "counts","er")
scatter(stats.df, "er","ribo")
scatter(stats.df, "mito","malat1")
scatter(stats.df, "counts","malat1")
scatter(stats.df, "features","malat1")
scatter(stats.df, "cells","features")
scatter(stats.df, "cells","counts")
scatter(stats.df, "cells","ribo")


## Scatter plots per tissue facet
library(ggrepel)

scatter.rank <- function(stats.df, y, bars = TRUE) {
    varmin= paste0(y,".10")
    varmax= paste0(y,".90")
    view.df = stats.df %>% group_by(tissue) %>% mutate(rank = rank(!!rlang::sym(y), ties.method="first"))
    scatter.plot = ggplot(view.df, aes(x=rank, y=!!rlang::sym(y), label=sample_id)) +
        geom_point()  +
        geom_label_repel(max.overlaps=2)
        if(bars){
                  scatter.plot = scatter.plot + geom_errorbar(aes(ymin=.data[[varmin]], ymax=.data[[varmax]]), width=.2,
                      position=position_dodge(0.05))
        }


        scatter.plot = scatter.plot + facet_wrap(~tissue, scales = "free_x")
    ggsave(paste0("figures/qc/rank-tissue_", y,".png"), height = 20, width = 20)
}




scatter.rank(stats.df, "counts")
scatter.rank(stats.df, "features")
scatter.rank(stats.df, "mito")
scatter.rank(stats.df, "er")
scatter.rank(stats.df, "ribo")
scatter.rank(stats.df, "malat1")
scatter.rank(stats.df, "cells", bars = FALSE)


filters = list(percent.mt = mito.filter, percent.ribo = ribo.filter)
message("intercept")
for (.cov in names(filters)) {
    ghisto = list()
    message(.cov)
    for (n in tissues.available) {
    message(n)
        ghisto[[n]] = ggplot(subset(df[df$mask.l3,], tissue == n), aes(x=!!rlang::sym(.cov)))  +
            geom_histogram() +geom_vline(xintercept=filters[[.cov]][[n]], color="red") + theme_classic() + theme(axis.text.x = element_text(angle = 45, vjust = 1, hjust=1))  + ggtitle(n)
    }
    gall = Reduce(`+`, ghisto) +   plot_layout(ncol=5) + plot_annotation(title = paste0('Post-level3 QC ', .cov))
    ggsave(paste0("figures/qc/dataset/histo-",.cov,"-l3qc-all-intercept.png"), width = 12, height = 8, create.dir=TRUE)
}


library(patchwork)

scatter.tissue <- function(stats.df, x, y, .tissue) {
    unique.sample_ides = length(unique(stats.df$sample_id))
    scatter.plot = ggplot(stats.df, aes(x=!!rlang::sym(x), y=!!rlang::sym(y), col= cell_type)) +
        geom_point(size=0.5, stroke = 0) + theme_classic()  + theme(axis.text.x = element_text(angle = 45, vjust = 1, hjust=1)) + guides(colour = guide_legend(override.aes = list(size=5))) +
        facet_wrap(~sample_id, ncol = 10)
    ggsave(paste0("figures/qc/dataset/tissue/",.tissue,"/scatter-", .tissue,"_", x,"-", y,".png"), height = (as.integer(unique.sample_ides/10)+1)*3, width = 20, create.dir = TRUE)
}



for (n in tissues.available) {
    message(n)
    .df <- subset(df, tissue == n)
    .df$cell_type = .df$tissue_cell_type
    ct.white = .df%>% group_by(tissue_cell_type) %>% tally() %>% top_n(10)
    .df$cell_type[!(.df$tissue_cell_type %in% ct.white$tissue_cell_type)] = "other"
    scatter.tissue(.df, "nCount_RNA", "nFeature_RNA", n)
    scatter.tissue(.df, "nFeature_RNA", "percent.mt", n)
    scatter.tissue(.df, "nFeature_RNA", "percent.ribo", n)
    scatter.tissue(.df, "nFeature_RNA", "percent.er", n)
    if(TRUE){
        for (b in unique(.df[["sample_id"]])) {
            ..df = subset(.df, sample_id == b)
            p1 = ggplot(..df,
                        aes(x=nCount_RNA,
                            y=nFeature_RNA,
                            col= cell_type)) +
                geom_point() + theme_classic() + theme(legend.position = "none")
            p2 = ggplot(..df,
                        aes(x=nFeature_RNA,
                            y=percent.mt,
                            col= cell_type)) +
                geom_point() + theme_classic() + theme(legend.position = "none")
            p3 = ggplot(..df,
                        aes(x=nFeature_RNA,
                            y=percent.ribo,
                            col= cell_type)) +
                geom_point() + theme_classic() + theme(legend.position = "none")
            p4 = ggplot(..df,
                        aes(x=nCount_RNA,
                            y=percent.malat1,
                            col= cell_type)) +
                geom_point() + guides(colour = guide_legend(override.aes = list(size=5))) + theme_classic()
            p = p1 + p2 + p3 + p4 + plot_layout(ncol=4)
            ggsave(paste0("figures/qc/dataset/tissue/",n,"/samples/scatter-", n, "-", b,"_allQC.png"),
                   height = 5.5, width = 20, create.dir = TRUE)
        }
    }


}
