import { combineReducers, createStore } from 'redux';
import AccountInfoReducer from './Reducers/AccountInfoReducer';
import LayoutReducer from './Reducers/LayoutReducer';
import MMStatsReducer from './Reducers/MMStatsReducer';
import OrdersReducer from './Reducers/OrdersReducer';
import PositionsReducer from './Reducers/PositionsReducer';
import StrategiesReducer from './Reducers/StrategiesReducer';
import WalletsReducer from './Reducers/WalletsReducer';

export default createStore(
  combineReducers({
    layout: LayoutReducer,
    account: AccountInfoReducer,
    mmstats: MMStatsReducer,
    orders: OrdersReducer,
    strategies: StrategiesReducer,
    positions: PositionsReducer,
    wallets: WalletsReducer,
  }),
);
