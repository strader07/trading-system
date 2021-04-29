import _ from 'lodash';

const SET_ORDERS = '@Redux/Orders/SET_ORDERS';

const DEFAULT_STATE = {
  orders: [],
  latestUpdate: new Date().toUTCString(),
};

export default function OrdersReducer(state = DEFAULT_STATE, action) {
  if (action.type === SET_ORDERS) {
    return _.assign({}, state, action.payload);
  } else {
    return state;
  }
}

export function setOrders(str) {
  let payload = DEFAULT_STATE;
  try {
    const obj = JSON.parse(str || '{}');
    if (!!obj.data) {
      payload.orders = Object.values(obj.data);
    }
    if (typeof obj.date === 'string') {
      payload.latestUpdate = obj.date;
    }
  } catch (err) {
    console.error(err);
  }
  return { type: SET_ORDERS, payload };
}
