import _ from 'lodash';

const SET_POSITIONS = '@Redux/Positions/SET_POSITIONS';

const DEFAULT_STATE = {
  positions: [],
  latestUpdate: new Date().toUTCString(),
};

export default function PositionsReducer(state = DEFAULT_STATE, action) {
  if (action.type === SET_POSITIONS) {
    return _.assign({}, state, action.payload);
  } else {
    return state;
  }
}

export function setPositions(str) {
  let payload = DEFAULT_STATE;
  try {
    const obj = JSON.parse(str || '{}');
    if (Array.isArray(obj.data)) {
      payload.positions = obj.data;
    }
    if (typeof obj.date === 'string') {
      payload.latestUpdate = obj.date;
    }
  } catch (err) {
    console.error(err);
  }
  return { type: SET_POSITIONS, payload };
}
