// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/*
 * Contract interface for receivers of tokens that
 * comply with ERC-677.
 * See https://github.com/ethereum/EIPs/issues/677 for details.
 */
interface IERC677TransferReceiver {
    function tokenFallback(
        address from,
        uint256 amount,
        bytes calldata data
    ) external returns (bool);
}
