from .types.market_header import MarketHeader


class MarketMetadata:
    def __init__(self, header: MarketHeader):
        self.base_mint = header.base_params.mint_key
        self.quote_mint = header.quote_params.mint_key
        self.base_decimals = header.base_params.decimals
        self.quote_decimals = header.quote_params.decimals
        self.base_atoms_per_raw_base_unit = 10**self.base_decimals
        self.quote_atoms_per_quote_unit = 10**self.quote_decimals
        self.quote_atoms_per_quote_lot = header.quote_lot_size
        self.base_atoms_per_base_lot = header.base_lot_size
        self.tick_size_in_quote_atoms_per_base_unit = (
            header.tick_size_in_quote_atoms_per_base_unit
        )
        self.raw_base_units_per_base_unit = max(header.raw_base_units_per_base_unit, 1)

        if (
            self.base_atoms_per_raw_base_unit
            * self.raw_base_units_per_base_unit
            % self.base_atoms_per_base_lot
            != 0
        ):
            raise ValueError("Invalid base lot size (in base atoms per base lot)")

        self.num_base_lots_per_base_unit = (
            self.base_atoms_per_raw_base_unit * self.raw_base_units_per_base_unit
        ) // self.base_atoms_per_base_lot
        self.market_size_params = header.market_size_params

    def raw_base_units_to_base_lots_rounded_down(self, raw_base_units):
        base_units = raw_base_units / self.raw_base_units_per_base_unit
        return int(base_units * self.num_base_lots_per_base_unit)

    def raw_base_units_to_base_lots_rounded_up(self, raw_base_units):
        base_units = raw_base_units / self.raw_base_units_per_base_unit
        return int(
            (base_units * self.num_base_lots_per_base_unit) + 0.5
        )  # using 0.5 to achieve rounding up

    def base_atoms_to_base_lots_rounded_down(self, base_atoms):
        return base_atoms // self.base_atoms_per_base_lot

    def base_atoms_to_base_lots_rounded_up(self, base_atoms):
        return (
            base_atoms + self.base_atoms_per_base_lot - 1
        ) // self.base_atoms_per_base_lot

    def base_lots_to_base_atoms(self, base_lots):
        return base_lots * self.base_atoms_per_base_lot

    def quote_units_to_quote_lots(self, quote_units):
        return int(
            quote_units
            * (self.quote_atoms_per_quote_unit / self.quote_atoms_per_quote_lot)
        )

    def quote_atoms_to_quote_lots_rounded_down(self, quote_atoms):
        return quote_atoms // self.quote_atoms_per_quote_lot

    def quote_atoms_to_quote_lots_rounded_up(self, quote_atoms):
        return (
            quote_atoms + self.quote_atoms_per_quote_lot - 1
        ) // self.quote_atoms_per_quote_lot

    def quote_lots_to_quote_atoms(self, quote_lots):
        return quote_lots * self.quote_atoms_per_quote_lot

    def base_atoms_to_raw_base_units_as_float(self, base_atoms):
        return base_atoms / self.base_atoms_per_raw_base_unit

    def base_lots_to_raw_base_units_as_float(self, base_lots):
        return self.base_atoms_to_raw_base_units_as_float(
            self.base_lots_to_base_atoms(base_lots)
        )

    def quote_atoms_to_quote_units_as_float(self, quote_atoms):
        return quote_atoms / self.quote_atoms_per_quote_unit

    def base_lots_and_price_to_quote_atoms(self, base_lots, price_in_ticks):
        return (
            base_lots
            * price_in_ticks
            * self.tick_size_in_quote_atoms_per_base_unit
            // self.num_base_lots_per_base_unit
        )

    def float_price_to_ticks_rounded_down(self, price):
        result = (
            price * self.raw_base_units_per_base_unit * self.quote_atoms_per_quote_unit
        ) / self.tick_size_in_quote_atoms_per_base_unit
        return int(result)

    def float_price_to_ticks_rounded_up(self, price):
        result = (
            price * self.raw_base_units_per_base_unit * self.quote_atoms_per_quote_unit
        ) / self.tick_size_in_quote_atoms_per_base_unit
        return int(result + 0.5)  # using 0.5 to achieve rounding up

    def ticks_to_float_price(self, ticks):
        return (
            ticks
            * self.tick_size_in_quote_atoms_per_base_unit
            / (self.quote_atoms_per_quote_unit * self.raw_base_units_per_base_unit)
        )

    def raw_base_units_per_base_lot(self):
        return self.base_atoms_per_base_lot / self.base_atoms_per_raw_base_unit

    def quote_units_per_raw_base_unit_per_tick(self):
        return self.tick_size_in_quote_atoms_per_base_unit / (
            self.quote_atoms_per_quote_unit * self.raw_base_units_per_base_unit
        )
