import * as React from "react";
import TextField from "material-ui/TextField";
import { Component } from "react";

import FilterCard from "../../components/cards/FilterCard";
import FormSpacer from "../../components/FormSpacer";
import MultiSelectField from "../../components/MultiSelectField";
import SingleSelectField from "../../components/SingleSelectField";
import PriceField from "../../components/PriceField";
import i18n from "../../i18n";

interface ProductFiltersState {
  debounceTimeout?: any;
  highlighted: string;
  name: string;
  price_min: string;
  price_max: string;
  productTypes: Array<string>;
  published: string;
}
interface ProductFiltersProps {
  productTypes: Array<{
    id: string;
    name: string;
  }>;
  formState?: ProductFiltersState;
  handleSubmit(formState: any);
  handleClear();
}

export class ProductFilters extends Component<
  ProductFiltersProps,
  ProductFiltersState
> {
  static defaultState = {
    highlighted: "",
    name: "",
    price_max: "",
    price_min: "",
    productTypes: [],
    published: ""
  };
  constructor(props) {
    super(props);
    this.state = { ...ProductFilters.defaultState, ...props.formState };
  }

  render() {
    const { handleSubmit, productTypes, handleClear, formState } = this.props;
    const publishingStatuses = [
      {
        label: i18n.t("Published", { context: "Product publishing status" }),
        value: "1"
      },
      {
        label: i18n.t("Not published", {
          context: "Product publishing status"
        }),
        value: "0"
      },
      {
        label: i18n.t("All", {
          context: "Product publishing status"
        }),
        value: ""
      }
    ];
    const highlightingStatuses = [
      {
        label: i18n.t("Highlighted", {
          context: "Product highlighting status"
        }),
        value: "1"
      },
      {
        label: i18n.t("Not highlighted", {
          context: "Product highlighting status"
        }),
        value: "0"
      },
      {
        label: i18n.t("All", {
          context: "Product highlighting status"
        }),
        value: ""
      }
    ];

    const handleInputChange = event => {
      const { name, value } = event.target;
      const debounceTimeout = setTimeout(() => {
        handleSubmit({
          formData: { [name]: value }
        });
      }, 500);
      clearTimeout(this.state.debounceTimeout);
      this.setState({
        [name]: value,
        debounceTimeout
      });
    };

    const handleClearButtonClick = () => {
      this.setState(ProductFilters.defaultState);
      handleClear();
    };

    return (
      <FilterCard handleClear={handleClearButtonClick}>
        <TextField
          fullWidth
          name="name"
          label={i18n.t("Name", {
            context: "Product filter field label"
          })}
          onChange={handleInputChange}
          value={this.state.name || ""}
        />
        <FormSpacer />
        <MultiSelectField
          label={i18n.t("Product type", {
            context: "Product filter field label"
          })}
          choices={productTypes.map(type => ({
            value: type.id,
            label: type.name
          }))}
          name="productTypes"
          onChange={handleInputChange}
          value={this.state.productTypes || []}
        />
        <FormSpacer />
        <PriceField
          currencySymbol="USD"
          label={i18n.t("Price")}
          name="price"
          onChange={handleInputChange}
          value={{
            min: this.state.price_min,
            max: this.state.price_max || ""
          }}
        />
        <FormSpacer />
        <SingleSelectField
          label={i18n.t("Published", {
            context: "Product filter field label"
          })}
          choices={publishingStatuses}
          name="published"
          onChange={handleInputChange}
          value={this.state.published || ""}
        />
        <FormSpacer />
        <SingleSelectField
          label={i18n.t("Highlighted", {
            context: "Product filter field label"
          })}
          choices={highlightingStatuses}
          name="highlighted"
          onChange={handleInputChange}
          value={this.state.highlighted || ""}
        />
      </FilterCard>
    );
  }
}

export default ProductFilters;
