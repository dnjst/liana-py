from __future__ import annotations

from .liana_pipe import liana_pipe

from anndata import AnnData
from pandas import DataFrame, concat
from typing import Optional


class MethodMeta:
    """
    A Class used to store Method Metadata
    """

    def __init__(self,
                 method_name: str,
                 complex_cols: list,
                 add_cols: list,
                 fun,
                 magnitude: str | None,
                 magnitude_ascending: bool | None,
                 specificity: str | None,
                 specificity_ascending: bool | None,
                 permute: bool,
                 reference: str
                 ):
        """
        Parameters
        ----------
        method_name
            Name of the Method
        complex_cols
            Columns relevant for protein complexes
        add_cols
            Additional columns required by the method
        fun
            Interaction Scoring function
        magnitude
            Name of the `magnitude` Score (None if not present)
        magnitude_ascending
            Whether to rank `magnitude` in ascending manner (None if not relevant)
        specificity
            Name of the `specificity` Score if Present (None if not present)
        specificity_ascending
            Whether to rank `magnitude` in ascending manner  (None if not relevant)
        permute
            Whether it requires permutations
        reference
            Publication reference in Harvard style
        """
        self.method_name = method_name
        self.complex_cols = complex_cols
        self.add_cols = add_cols
        self.fun = fun
        self.magnitude = magnitude
        self.magnitude_ascending = magnitude_ascending
        self.specificity = specificity
        self.specificity_ascending = specificity_ascending
        self.permute = permute
        self.reference = reference

    # describe self
    def describe(self):
        """Briefly described the method"""
        print(
            f"{self.method_name} uses `{self.magnitude}` and `{self.specificity}`"
            f" as measures of expression strength and interaction specificity, respectively"
        )

    def reference(self):
        """Prints out reference in Harvard format"""
        print(self.reference)

    def get_meta(self):
        """Returns method metadata as pandas row"""
        meta = DataFrame([{"Method Name": self.method_name,
                           "Magnitude Score": self.magnitude,
                           "Specificity Score": self.specificity,
                           "Reference": self.reference
                           }])
        return meta


class Method(MethodMeta):
    """
    A class used to generate Method instances
    """

    def __init__(self, _SCORE):
        super().__init__(method_name=_SCORE.method_name,
                         complex_cols=_SCORE.complex_cols,
                         add_cols=_SCORE.add_cols,
                         fun=_SCORE.fun,
                         magnitude=_SCORE.magnitude,
                         magnitude_ascending=_SCORE.magnitude_ascending,
                         specificity=_SCORE.specificity,
                         specificity_ascending=_SCORE.specificity_ascending,
                         permute=_SCORE.permute,
                         reference=_SCORE.reference
                         )
        self._SCORE = _SCORE

    def __call__(self,
                 adata: AnnData,
                 groupby: str,
                 resource_name: str = 'consensus',
                 expr_prop: float = 0.1,
                 base: float = 2.718281828459045,
                 use_raw: Optional[bool] = False,
                 layer: Optional[str] = None,
                 de_method='t-test',
                 verbose: Optional[bool] = False,
                 n_perms: int = 1000,
                 seed: int = 1337,
                 resource: Optional[DataFrame] = None,
                 copy=False) -> AnnData:
        """
        Parameters
        ----------
        adata
            Annotated data object.
        groupby
            The key of the observations grouping to consider.
        resource_name
            Name of the resource to be loaded and use for ligand-receptor inference.
        expr_prop
            Minimum expression proportion for the ligands/receptors (and their subunits) in the
             corresponding cell identities. Set to `0`, to return unfiltered results.
        base
            Exponent base used to reverse the log-transformation of matrix. Note that this is
            relevant only for the `logfc` method.
        use_raw
            Use raw attribute of adata if present.
        layer
            Layer in anndata.AnnData.layers to use. If None, use anndata.AnnData.X.
        de_method
            Differential expression method. `scanpy.tl.rank_genes_groups` is used to rank genes
            according to 1vsRest. The default method is 't-test'. Only relevant if p-values
            are included in `supp_cols`
        verbose
            Verbosity flag
        n_perms
            Number of permutations for the permutation test. Note that this is relevant
            only for permutation-based methods - e.g. `CellPhoneDB`
        seed
            Random seed for reproducibility.
        resource
            Parameter to enable external resources to be passed. Expects a pandas dataframe
            with [`ligand`, `receptor`] columns. None by default. If provided will overrule
            the resource requested via `resource_name`
        copy
            If true return `DataFrame` with results, else assign to `.uns`.

        Returns
        -------
        If ``copy = True``, returns a `DataFrame` with ligand-receptor results
        Otherwise, modifies the ``adata`` object with the following key:
            - :attr:`anndata.AnnData.uns` ``['liana_res']`` with the aforementioned DataFrame
        """
        liana_res = liana_pipe(adata=adata,
                               groupby=groupby,
                               resource_name=resource_name,
                               resource=resource,
                               expr_prop=expr_prop,
                               supp_cols=['ligand_pvals', 'receptor_pvals'],
                               base=base,
                               de_method=de_method,
                               verbose=verbose,
                               _score=self._SCORE,
                               n_perms=n_perms,
                               seed=seed,
                               use_raw=use_raw,
                               layer=layer,
                               )
        if not copy:
            adata.uns['liana_res'] = liana_res
            return adata
        else:
            return liana_res


def _show_methods(methods):
    return concat([method.get_meta() for method in methods])
